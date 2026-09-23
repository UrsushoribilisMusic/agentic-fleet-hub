import Foundation

/// Orchestrates the on-device bone ingestion pipeline:
/// extract → chunk → build → install → enrich (background, optional).
///
/// All UI-facing state is published on the main actor. Heavy CPU work (extract,
/// chunk, build) is dispatched to background threads via Task.detached.
@MainActor
final class BoneIngestionManager: ObservableObject {
    static let shared = BoneIngestionManager()

    // MARK: - Stage

    enum Stage: Equatable {
        case idle
        case extracting
        case chunking
        case building
        case done(BoneEntry)
        case failed(String)

        var isActive: Bool {
            switch self {
            case .extracting, .chunking, .building: return true
            default: return false
            }
        }
    }

    enum Step { case extract, chunk, build, enrich }

    enum StepStatus { case pending, inProgress, done }

    // MARK: - Published state

    @Published var stage: Stage = .idle
    /// Non-nil while enrichment is running; nil when enrichment is idle or complete.
    @Published var enrichmentProgress: (done: Int, total: Int)? = nil
    /// Controls the GiveABoneView sheet from anywhere (e.g. share-sheet open).
    @Published var isShowingImport = false

    // MARK: - Private

    private var ingestionTask: Task<Void, Never>?
    private init() {}

    // MARK: - Public API

    func ingest(url: URL, model: CanisModel = .apertus) {
        ingestionTask?.cancel()
        Task { await BoneEnricher.shared.cancel() }
        enrichmentProgress = nil
        stage = .extracting

        ingestionTask = Task {
            do {
                let accessed = url.startAccessingSecurityScopedResource()
                defer { if accessed { url.stopAccessingSecurityScopedResource() } }

                // Stage 1: Extract (background thread)
                let pages = try await Task.detached(priority: .userInitiated) {
                    try BoneExtractor().extract(url)
                }.value
                guard !Task.isCancelled else { return }

                // Stage 2: Chunk (background thread)
                stage = .chunking
                let chunks = await Task.detached(priority: .userInitiated) {
                    BoneChunker().chunk(pages)
                }.value
                guard !Task.isCancelled else { return }

                let docTitle = url.deletingPathExtension().lastPathComponent
                let sourceName = url.lastPathComponent

                // Stage 3: Build (background thread)
                stage = .building
                let tmpURL = try await Task.detached(priority: .userInitiated) {
                    try BoneBuilder().build(
                        chunks: chunks,
                        docTitle: docTitle,
                        sourceName: sourceName
                    )
                }.value
                guard !Task.isCancelled else { return }

                // Stage 4: Install (main actor — KnowledgePackStore is @MainActor)
                let entry = try KnowledgePackStore.shared.installBone(
                    from: tmpURL,
                    name: docTitle,
                    docCount: 1,
                    wikiSectionCount: chunks.count
                )
                guard !Task.isCancelled else { return }

                stage = .done(entry)

                // Stage 5: Enrich titles (background actor, non-blocking)
                let boneURL = KnowledgePackStore.bonesDirectoryURL
                    .appendingPathComponent("\(entry.id).sqlite")
                let chunkTotal = chunks.count
                enrichmentProgress = (done: 0, total: chunkTotal)

                await BoneEnricher.shared.enrich(
                    boneURL: boneURL,
                    model: model,
                    onProgress: { done, total in
                        Task { @MainActor in
                            BoneIngestionManager.shared.enrichmentProgress =
                                done < total ? (done, total) : nil
                        }
                    }
                )

            } catch {
                guard !Task.isCancelled else { return }
                stage = .failed(error.localizedDescription)
            }
        }
    }

    func skipEnrichment() {
        Task { await BoneEnricher.shared.cancel() }
        enrichmentProgress = nil
    }

    /// Cancel any in-flight ingestion and reset to idle.
    func cancel() {
        ingestionTask?.cancel()
        ingestionTask = nil
        Task { await BoneEnricher.shared.cancel() }
        enrichmentProgress = nil
        stage = .idle
    }

    /// Reset to idle state (e.g. after dismissing the import sheet).
    func reset() {
        cancel()
    }

    // MARK: - Step status helper

    func stepStatus(_ step: Step) -> StepStatus {
        switch stage {
        case .idle:
            return .pending
        case .extracting:
            return step == .extract ? .inProgress : .pending
        case .chunking:
            switch step {
            case .extract: return .done
            case .chunk: return .inProgress
            case .build, .enrich: return .pending
            }
        case .building:
            switch step {
            case .extract, .chunk: return .done
            case .build: return .inProgress
            case .enrich: return .pending
            }
        case .done:
            switch step {
            case .extract, .chunk, .build: return .done
            case .enrich: return enrichmentProgress == nil ? .done : .inProgress
            }
        case .failed:
            return .pending
        }
    }
}
