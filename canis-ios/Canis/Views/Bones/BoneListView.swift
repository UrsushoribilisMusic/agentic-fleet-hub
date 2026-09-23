import SwiftUI

struct BoneListView: View {
    @EnvironmentObject private var store: KnowledgePackStore
    @EnvironmentObject private var ingestion: BoneIngestionManager
    @AppStorage("canis.activeModelID") private var activeModelID: String = CanisModel.apertus.rawValue
    @State private var renameEntry: BoneEntry?
    @State private var renameDraft = ""

    private var activeModel: CanisModel {
        CanisModel(rawValue: activeModelID) ?? .apertus
    }

    var body: some View {
        NavigationStack {
            Group {
                if store.bones.isEmpty {
                    emptyState
                } else {
                    List {
                        ForEach(store.bones) { bone in
                            let isEnriching = ingestion.enrichingBoneID == bone.id
                            let enrichProgress = isEnriching ? ingestion.enrichmentProgress : nil
                            BoneRowView(
                                bone: bone,
                                onActivate: { try? store.setActiveBone(id: bone.id) },
                                enrichmentProgress: enrichProgress,
                                onCancelEnrichment: isEnriching ? { ingestion.skipEnrichment() } : nil
                            )
                            .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                                if !bone.isBuiltIn {
                                    Button(role: .destructive) {
                                        try? store.deleteBone(id: bone.id)
                                    } label: {
                                        Label("Delete", systemImage: "trash")
                                    }
                                }
                                Button {
                                    renameDraft = bone.name
                                    renameEntry = bone
                                } label: {
                                    Label("Rename", systemImage: "pencil")
                                }
                                .tint(.blue)
                                if !isEnriching {
                                    Button {
                                        ingestion.enrichBone(bone, model: activeModel)
                                    } label: {
                                        Label("Generate Titles", systemImage: "sparkles.text.page")
                                    }
                                    .tint(.indigo)
                                }
                            }
                        }
                    }
                    .listStyle(.insetGrouped)
                }
            }
            .navigationTitle("Bones")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        ingestion.reset()
                        ingestion.isShowingImport = true
                    } label: {
                        Image(systemName: "plus")
                    }
                    .accessibilityLabel("Give a bone")
                }
            }
        }
        .alert("Rename Bone", isPresented: Binding(
            get: { renameEntry != nil },
            set: { if !$0 { renameEntry = nil } }
        )) {
            TextField("Name", text: $renameDraft)
            Button("Rename") {
                if let entry = renameEntry, !renameDraft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    try? store.renameBone(id: entry.id, name: renameDraft.trimmingCharacters(in: .whitespacesAndNewlines))
                }
                renameEntry = nil
            }
            Button("Cancel", role: .cancel) { renameEntry = nil }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "books.vertical")
                .font(.system(size: 52))
                .foregroundStyle(.secondary)
            Text("No bones yet")
                .font(.title3.bold())
            Text("Import a PDF, text, or Markdown file to create an offline knowledge pack.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            Button {
                ingestion.reset()
                ingestion.isShowingImport = true
            } label: {
                Label("Give the dog a bone", systemImage: "books.vertical.badge.plus")
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }
}

// MARK: - Bone Row

struct BoneRowView: View {
    let bone: BoneEntry
    let onActivate: () -> Void
    var enrichmentProgress: (done: Int, total: Int)? = nil
    var onCancelEnrichment: (() -> Void)? = nil

    private var sizeString: String {
        ByteCountFormatter.string(fromByteCount: bone.size, countStyle: .file)
    }

    var body: some View {
        VStack(spacing: 0) {
            Button(action: onActivate) {
                HStack(spacing: 12) {
                    Image(systemName: bone.isBuiltIn ? "brain" : "books.vertical.fill")
                        .font(.title3)
                        .foregroundStyle(bone.isActive ? Color.accentColor : Color(.secondaryLabel))
                        .frame(width: 32)

                    VStack(alignment: .leading, spacing: 2) {
                        HStack(spacing: 6) {
                            Text(bone.name)
                                .font(.body)
                                .foregroundStyle(.primary)
                            if bone.isActive {
                                Text("Active")
                                    .font(.caption2.weight(.semibold))
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Color.accentColor.opacity(0.15))
                                    .foregroundStyle(.tint)
                                    .clipShape(Capsule())
                            }
                            if bone.isBuiltIn {
                                Text("Built-in")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        Text("\(bone.wikiSectionCount) chunks · \(sizeString)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    Spacer()

                    if bone.isActive {
                        Image(systemName: "checkmark")
                            .foregroundStyle(.tint)
                            .font(.body.weight(.semibold))
                    }
                }
            }
            .buttonStyle(.plain)

            if let progress = enrichmentProgress {
                Divider()
                HStack(spacing: 8) {
                    ProgressView(value: Double(progress.done), total: Double(max(progress.total, 1)))
                        .tint(.indigo)
                    Text("\(progress.done)/\(progress.total)")
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(.secondary)
                        .fixedSize()
                    Button("Cancel") { onCancelEnrichment?() }
                        .font(.caption)
                        .buttonStyle(.borderless)
                        .foregroundStyle(.secondary)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
            }
        }
    }
}

#Preview {
    BoneListView()
        .environmentObject(KnowledgePackStore.shared)
        .environmentObject(BoneIngestionManager.shared)
}
