import Foundation

enum KnowledgePackState: Equatable {
    case notInstalled
    case checking
    case downloading(Double)
    case ready(version: Int, docCount: Int, wikiSectionCount: Int)
    case failed(String)

    var isReady: Bool {
        if case .ready = self { return true }
        return false
    }
}

struct BoneEntry: Codable, Identifiable, Equatable {
    let id: String
    var name: String
    let docCount: Int
    let wikiSectionCount: Int
    var size: Int64
    let createdAt: Date
    var isActive: Bool
    let isBuiltIn: Bool
}

@MainActor
final class KnowledgePackStore: ObservableObject {
    static let shared = KnowledgePackStore()

    // MARK: - Static URLs

    nonisolated static var directoryURL: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("knowledge-packs", isDirectory: true)
    }

    /// Legacy path; kept for the token-download flow and pre-BONE-05 installs.
    nonisolated static var currentPackURL: URL {
        directoryURL.appendingPathComponent("current.sqlite")
    }

    nonisolated static var bonesDirectoryURL: URL {
        directoryURL.appendingPathComponent("bones", isDirectory: true)
    }

    nonisolated static var bonesIndexURL: URL {
        directoryURL.appendingPathComponent("bones-index.json")
    }

    /// URL of the active bone. Falls back to `currentPackURL` when no
    /// bones-index.json exists (backward-compat with pre-BONE-05 installs).
    nonisolated static var activePackURL: URL {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        guard let data = try? Data(contentsOf: bonesIndexURL),
              let entries = try? decoder.decode([BoneEntry].self, from: data),
              let active = entries.first(where: { $0.isActive })
        else {
            return currentPackURL
        }
        return bonesDirectoryURL.appendingPathComponent("\(active.id).sqlite")
    }

    // MARK: - Constants

    /// Stable deterministic UUID for the bundled Robot Ross ATF bone.
    static let builtinRobotRossID = "00000000-0000-0000-0000-000000000001"
    private static let bundledPackName = "robot-ross-atf"
    private static let bundledPackVersion = 1
    private static let bundledDocCount = 14
    private static let bundledWikiSectionCount = 83

    private static let tokenKey = "canis.apiToken"
    private static let apiBaseURLKey = "canis.apiBaseURL"
    private static let legacyMetadataFile = "installed-pack.json"

    // MARK: - Published state

    @Published private(set) var state: KnowledgePackState = .checking
    /// All installed bones, including the built-in Robot Ross bone.
    @Published private(set) var bones: [BoneEntry] = []
    @Published var apiToken: String = ""
    @Published var apiBaseURLString: String = Config.CanisAPI.defaultBaseURL

    private init() {}

    // MARK: - Setup

    func setup() {
        apiToken = UserDefaults.standard.string(forKey: Self.tokenKey) ?? ""
        apiBaseURLString = UserDefaults.standard.string(forKey: Self.apiBaseURLKey) ?? Config.CanisAPI.defaultBaseURL
        createDirectoriesIfNeeded()
        seedBundledPackIfNeeded()
        bones = readBonesIndex()
        state = deriveState()
    }

    // MARK: - Multi-bone CRUD

    /// Install a bone produced by BoneBuilder. Moves the sqlite from `tmpURL` into
    /// `bones/<uuid>.sqlite` and registers it in the index.
    /// If no bone is currently active, the new bone becomes active.
    @discardableResult
    func installBone(
        from tmpURL: URL,
        name: String,
        docCount: Int,
        wikiSectionCount: Int
    ) throws -> BoneEntry {
        let id = UUID().uuidString
        let destination = Self.bonesDirectoryURL.appendingPathComponent("\(id).sqlite")
        try FileManager.default.createDirectory(at: Self.bonesDirectoryURL, withIntermediateDirectories: true)
        try FileManager.default.moveItem(at: tmpURL, to: destination)
        let shouldActivate = !bones.contains { $0.isActive }
        let entry = BoneEntry(
            id: id,
            name: name,
            docCount: docCount,
            wikiSectionCount: wikiSectionCount,
            size: fileSize(at: destination),
            createdAt: Date(),
            isActive: shouldActivate,
            isBuiltIn: false
        )
        bones.append(entry)
        try writeBonesIndex()
        if shouldActivate {
            state = .ready(version: 1, docCount: docCount, wikiSectionCount: wikiSectionCount)
        }
        return entry
    }

    /// Change the active bone. The retriever picks up the new bone on next instantiation.
    func setActiveBone(id: String) throws {
        guard let idx = bones.firstIndex(where: { $0.id == id }) else { return }
        for i in bones.indices { bones[i].isActive = false }
        bones[idx].isActive = true
        try writeBonesIndex()
        let b = bones[idx]
        state = .ready(version: 1, docCount: b.docCount, wikiSectionCount: b.wikiSectionCount)
    }

    func renameBone(id: String, name: String) throws {
        guard let idx = bones.firstIndex(where: { $0.id == id }) else { return }
        bones[idx].name = name
        try writeBonesIndex()
    }

    /// Delete a user bone. Built-in bones cannot be deleted.
    /// When the deleted bone was active, the built-in bone (or the first remaining
    /// bone) is promoted to active so the retriever never goes dark.
    func deleteBone(id: String) throws {
        guard let idx = bones.firstIndex(where: { $0.id == id }) else { return }
        let entry = bones[idx]
        guard !entry.isBuiltIn else { return }
        let wasActive = entry.isActive
        try? FileManager.default.removeItem(
            at: Self.bonesDirectoryURL.appendingPathComponent("\(entry.id).sqlite")
        )
        bones.remove(at: idx)
        if wasActive {
            if let builtinIdx = bones.firstIndex(where: { $0.isBuiltIn }) {
                bones[builtinIdx].isActive = true
            } else if !bones.isEmpty {
                bones[0].isActive = true
            }
        }
        try writeBonesIndex()
        state = deriveState()
    }

    // MARK: - Settings

    func saveSettings(token: String, apiBaseURLString: String) {
        apiToken = token.trimmingCharacters(in: .whitespacesAndNewlines)
        self.apiBaseURLString = apiBaseURLString.trimmingCharacters(in: .whitespacesAndNewlines)
        UserDefaults.standard.set(apiToken, forKey: Self.tokenKey)
        UserDefaults.standard.set(self.apiBaseURLString, forKey: Self.apiBaseURLKey)
    }

    func saveToken(_ token: String) {
        saveSettings(token: token, apiBaseURLString: apiBaseURLString)
    }

    // MARK: - Legacy token-download (ModelHubView backward compat)

    func downloadLatest() async {
        let token = apiToken.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !token.isEmpty else {
            state = .failed("Paste the Canis session token before downloading the pack.")
            return
        }

        state = .checking
        do {
            let status = try await fetchStatus(token: token)
            guard status.version > 0, status.status == "ready" else {
                state = .failed("No ready pack is available yet.")
                return
            }

            state = .downloading(0)
            var request = URLRequest(url: try apiBaseURL().appendingPathComponent("pack/download"))
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            let (downloadURL, response) = try await URLSession.shared.download(for: request)
            guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
                state = .failed("Pack download failed.")
                return
            }

            try FileManager.default.createDirectory(at: Self.directoryURL, withIntermediateDirectories: true)
            let destination = Self.currentPackURL
            if FileManager.default.fileExists(atPath: destination.path) {
                try FileManager.default.removeItem(at: destination)
            }
            try FileManager.default.moveItem(at: downloadURL, to: destination)
            try writeLegacyMetadata(version: status.version, docCount: status.docCount, wikiSectionCount: status.wikiSectionCount)
            state = .ready(version: status.version, docCount: status.docCount, wikiSectionCount: status.wikiSectionCount)
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    /// Legacy: delete the active non-built-in bone. Falls back to clearing
    /// `current.sqlite` when no bones index exists (pre-BONE-05 installs).
    func deletePack() {
        if let idx = bones.firstIndex(where: { $0.isActive && !$0.isBuiltIn }) {
            try? deleteBone(id: bones[idx].id)
        } else {
            try? FileManager.default.removeItem(at: Self.currentPackURL)
            try? FileManager.default.removeItem(at: legacyMetadataURL)
            state = .notInstalled
        }
    }

    // MARK: - Private

    private func createDirectoriesIfNeeded() {
        try? FileManager.default.createDirectory(at: Self.directoryURL, withIntermediateDirectories: true)
        try? FileManager.default.createDirectory(at: Self.bonesDirectoryURL, withIntermediateDirectories: true)
    }

    private func seedBundledPackIfNeeded() {
        let builtinURL = Self.bonesDirectoryURL.appendingPathComponent("\(Self.builtinRobotRossID).sqlite")

        if !FileManager.default.fileExists(atPath: builtinURL.path),
           let bundled = Bundle.main.url(forResource: Self.bundledPackName, withExtension: "sqlite") {
            try? FileManager.default.copyItem(at: bundled, to: builtinURL)
        }

        var index = readBonesIndex()
        if !index.contains(where: { $0.id == Self.builtinRobotRossID }) {
            let hasActive = index.contains { $0.isActive }
            index.insert(
                BoneEntry(
                    id: Self.builtinRobotRossID,
                    name: "Robot Ross",
                    docCount: Self.bundledDocCount,
                    wikiSectionCount: Self.bundledWikiSectionCount,
                    size: fileSize(at: builtinURL),
                    createdAt: Date(),
                    isActive: !hasActive,
                    isBuiltIn: true
                ),
                at: 0
            )
            try? writeBonesIndexDirect(index)
        }

        // Also seed current.sqlite for the legacy token-download code path.
        if !FileManager.default.fileExists(atPath: Self.currentPackURL.path),
           let bundled = Bundle.main.url(forResource: Self.bundledPackName, withExtension: "sqlite") {
            try? FileManager.default.copyItem(at: bundled, to: Self.currentPackURL)
            try? writeLegacyMetadata(
                version: Self.bundledPackVersion,
                docCount: Self.bundledDocCount,
                wikiSectionCount: Self.bundledWikiSectionCount
            )
        }
    }

    private func deriveState() -> KnowledgePackState {
        let activeURL = Self.activePackURL
        guard FileManager.default.fileExists(atPath: activeURL.path) else {
            return .notInstalled
        }
        if let active = bones.first(where: { $0.isActive }) {
            return .ready(version: 1, docCount: active.docCount, wikiSectionCount: active.wikiSectionCount)
        }
        guard let data = try? Data(contentsOf: legacyMetadataURL),
              let meta = try? JSONDecoder().decode(LegacyMetadata.self, from: data)
        else {
            return .ready(version: 0, docCount: 0, wikiSectionCount: 0)
        }
        return .ready(version: meta.version, docCount: meta.docCount, wikiSectionCount: meta.wikiSectionCount)
    }

    // MARK: - Index helpers

    private func readBonesIndex() -> [BoneEntry] {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        guard let data = try? Data(contentsOf: Self.bonesIndexURL),
              let entries = try? decoder.decode([BoneEntry].self, from: data)
        else { return [] }
        return entries
    }

    private func writeBonesIndex() throws {
        try writeBonesIndexDirect(bones)
    }

    private func writeBonesIndexDirect(_ entries: [BoneEntry]) throws {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(entries)
        try data.write(to: Self.bonesIndexURL, options: .atomic)
    }

    // MARK: - Legacy metadata

    private struct LegacyMetadata: Codable {
        let version: Int
        let docCount: Int
        let wikiSectionCount: Int
        let installedAt: Date
    }

    private func writeLegacyMetadata(version: Int, docCount: Int, wikiSectionCount: Int) throws {
        let meta = LegacyMetadata(
            version: version, docCount: docCount,
            wikiSectionCount: wikiSectionCount, installedAt: Date()
        )
        let data = try JSONEncoder().encode(meta)
        try data.write(to: legacyMetadataURL, options: .atomic)
    }

    private var legacyMetadataURL: URL {
        Self.directoryURL.appendingPathComponent(Self.legacyMetadataFile)
    }

    // MARK: - Network helpers

    private struct PackStatus: Decodable {
        let version: Int
        let chunkCount: Int
        let docCount: Int
        let wikiSectionCount: Int
        let status: String
    }

    private func fetchStatus(token: String) async throws -> PackStatus {
        var request = URLRequest(url: try apiBaseURL().appendingPathComponent("pack/status"))
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.userAuthenticationRequired)
        }
        return try JSONDecoder().decode(PackStatus.self, from: data)
    }

    private func apiBaseURL() throws -> URL {
        guard let url = URL(string: apiBaseURLString.trimmingCharacters(in: .whitespacesAndNewlines)) else {
            throw URLError(.badURL)
        }
        return url
    }

    // MARK: - Utility

    private func fileSize(at url: URL) -> Int64 {
        (try? url.resourceValues(forKeys: [.fileSizeKey]).fileSize).map { Int64($0) } ?? 0
    }
}
