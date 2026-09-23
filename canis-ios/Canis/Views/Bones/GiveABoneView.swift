import SwiftUI
import UIKit
import UniformTypeIdentifiers

struct GiveABoneView: View {
    @EnvironmentObject private var ingestion: BoneIngestionManager
    @AppStorage("canis.activeModelID") private var activeModelID: String = CanisModel.apertus.rawValue
    @Environment(\.dismiss) private var dismiss
    @State private var showPicker = false

    private var activeModel: CanisModel {
        CanisModel(rawValue: activeModelID) ?? .apertus
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 28) {
                    header
                    if ingestion.stage != .idle {
                        progressSection
                    }
                    if let ep = ingestion.enrichmentProgress {
                        enrichmentSection(done: ep.done, total: ep.total)
                    }
                    actionSection
                }
                .padding(24)
                .animation(.easeInOut(duration: 0.2), value: ingestion.stage)
            }
            .navigationTitle("Give a Bone")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") {
                        ingestion.cancel()
                        dismiss()
                    }
                    .disabled(ingestion.stage.isActive)
                }
            }
            .sheet(isPresented: $showPicker) {
                DocumentPicker { url in
                    showPicker = false
                    ingestion.ingest(url: url, model: activeModel)
                }
                .ignoresSafeArea()
            }
        }
    }

    // MARK: - Subviews

    private var header: some View {
        VStack(spacing: 10) {
            Image(systemName: "books.vertical.fill")
                .font(.system(size: 52))
                .foregroundStyle(.tint)
            Text("Give the dog a bone")
                .font(.title2.bold())
            Text("Import a PDF, text, or Markdown file as a private, offline knowledge pack. Nothing leaves your phone.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(.top, 8)
    }

    private var progressSection: some View {
        VStack(alignment: .leading, spacing: 0) {
            stepRow("Extract text", step: .extract)
            Divider().padding(.leading, 44)
            stepRow("Chunk", step: .chunk)
            Divider().padding(.leading, 44)
            stepRow("Build bone", step: .build)
            Divider().padding(.leading, 44)
            stepRow("Enhance titles", step: .enrich, isOptional: true)
        }
        .background(Color(.secondarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private func stepRow(_ label: String, step: BoneIngestionManager.Step, isOptional: Bool = false) -> some View {
        let status = ingestion.stepStatus(step)
        return HStack(spacing: 12) {
            ZStack {
                switch status {
                case .done:
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                case .inProgress:
                    ProgressView()
                        .scaleEffect(0.85)
                case .pending:
                    Image(systemName: "circle")
                        .foregroundStyle(.tertiary)
                }
            }
            .frame(width: 22, height: 22)

            Text(isOptional ? "\(label) (optional)" : label)
                .font(.body)
                .foregroundStyle(status == .pending ? .secondary : .primary)

            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }

    private func enrichmentSection(done: Int, total: Int) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("Enhancing chunk titles")
                    .font(.subheadline.weight(.medium))
                Spacer()
                Text("\(done) / \(total)")
                    .font(.subheadline.monospacedDigit())
                    .foregroundStyle(.secondary)
                Button("Skip") {
                    ingestion.skipEnrichment()
                }
                .font(.subheadline)
                .buttonStyle(.borderless)
                .foregroundStyle(.secondary)
            }
            ProgressView(value: Double(done), total: Double(max(total, 1)))
                .tint(.accentColor)
            Text("Enrichment runs in the background and improves search quality over time.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding()
        .background(Color(.secondarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    @ViewBuilder
    private var actionSection: some View {
        switch ingestion.stage {
        case .idle:
            Button {
                showPicker = true
            } label: {
                Label("Choose Document", systemImage: "doc.badge.plus")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)

        case .extracting, .chunking, .building:
            Button(role: .cancel) {
                ingestion.cancel()
            } label: {
                Text("Cancel Import")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
            .controlSize(.large)
            .tint(.secondary)

        case .done(let entry):
            VStack(spacing: 12) {
                HStack(spacing: 6) {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                    Text("\u{201C}\(entry.name)\u{201D} is ready")
                        .font(.headline)
                }
                .frame(maxWidth: .infinity)
                Button {
                    ingestion.reset()
                    dismiss()
                } label: {
                    Text("Done")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                Button {
                    ingestion.reset()
                    showPicker = true
                } label: {
                    Text("Import Another")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .controlSize(.large)
            }

        case .failed(let message):
            VStack(spacing: 12) {
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                    Text(message)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                Button {
                    ingestion.reset()
                    showPicker = true
                } label: {
                    Text("Try Again")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
            }
        }
    }
}

// MARK: - Document Picker

struct DocumentPicker: UIViewControllerRepresentable {
    let onPick: (URL) -> Void

    func makeUIViewController(context: Context) -> UIDocumentPickerViewController {
        let mdType = UTType("net.daringfireball.markdown")
        let types: [UTType] = [.pdf, .plainText, .text, mdType].compactMap { $0 }
        let picker = UIDocumentPickerViewController(forOpeningContentTypes: types)
        picker.allowsMultipleSelection = false
        picker.shouldShowFileExtensions = true
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIDocumentPickerViewController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(onPick: onPick) }

    final class Coordinator: NSObject, UIDocumentPickerDelegate {
        let onPick: (URL) -> Void
        init(onPick: @escaping (URL) -> Void) { self.onPick = onPick }

        func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
            guard let url = urls.first else { return }
            onPick(url)
        }
    }
}

#Preview {
    GiveABoneView()
        .environmentObject(BoneIngestionManager.shared)
}
