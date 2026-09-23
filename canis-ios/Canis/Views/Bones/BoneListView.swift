import SwiftUI

struct BoneListView: View {
    @EnvironmentObject private var store: KnowledgePackStore
    @EnvironmentObject private var ingestion: BoneIngestionManager
    @State private var renameEntry: BoneEntry?
    @State private var renameDraft = ""

    var body: some View {
        NavigationStack {
            Group {
                if store.bones.isEmpty {
                    emptyState
                } else {
                    List {
                        ForEach(store.bones) { bone in
                            BoneRowView(bone: bone) {
                                try? store.setActiveBone(id: bone.id)
                            }
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

    private var sizeString: String {
        ByteCountFormatter.string(fromByteCount: bone.size, countStyle: .file)
    }

    var body: some View {
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
    }
}

#Preview {
    BoneListView()
        .environmentObject(KnowledgePackStore.shared)
        .environmentObject(BoneIngestionManager.shared)
}
