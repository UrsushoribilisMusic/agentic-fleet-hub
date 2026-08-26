import SwiftUI

struct ModelHubView: View {
    @EnvironmentObject private var downloads: ModelDownloadManager
    @EnvironmentObject private var knowledgePacks: KnowledgePackStore
    @Binding var activeModelID: String
    @State private var diskSpaceAlertBytes: Int64?
    @State private var packTokenDraft = ""
    @State private var packBaseURLDraft = Config.CanisAPI.defaultBaseURL
    #if DEBUG
    @AppStorage("canis.allowCellularDownload") private var cellularBypass = false
    #endif

    var body: some View {
        NavigationStack {
            List {
                if downloads.networkAvailable && !downloads.wifiDownloadAllowed {
                    Section {
                        Label("Wi-Fi required for model downloads.", systemImage: "wifi.exclamationmark")
                            .foregroundStyle(.orange)
                    }
                }

                Section("Active Model") {
                    Picker("Model", selection: $activeModelID) {
                        ForEach(CanisModel.allCases) { model in
                            Text(model.displayName).tag(model.rawValue)
                        }
                    }
                    .pickerStyle(.segmented)
                }

                Section("Download Hub") {
                    ForEach(CanisModel.allCases) { model in
                        ModelRowView(
                            model: model,
                            state: downloads.states[model.rawValue] ?? .notDownloaded,
                            bytesOnDisk: downloads.storageUsageBytes[model.rawValue] ?? 0,
                            isActive: activeModelID == model.rawValue,
                            start: { start(model) },
                            resume: { Task { await downloads.resumeDownload(model) } },
                            cancel: { Task { await downloads.cancelDownload(model) } },
                            delete: { Task { await downloads.deleteModel(model) } },
                            makeActive: { activeModelID = model.rawValue }
                        )
                    }
                }

                Section("Knowledge Pack") {
                    knowledgePackStatusRow

                    SecureField("Canis session token", text: $packTokenDraft)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .onSubmit {
                            savePackSettings()
                        }

                    TextField("Canis API URL", text: $packBaseURLDraft)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)
                        .onSubmit {
                            savePackSettings()
                        }

                    HStack {
                        Button {
                            savePackSettings()
                            Task { await knowledgePacks.downloadLatest() }
                        } label: {
                            Label("Download Latest", systemImage: "square.and.arrow.down")
                        }
                        .disabled(isPackBusy)

                        Spacer()

                        Button(role: .destructive) {
                            knowledgePacks.deletePack()
                        } label: {
                            Image(systemName: "trash")
                        }
                        .disabled(!knowledgePacks.state.isReady || isPackBusy)
                        .accessibilityLabel("Delete knowledge pack")
                    }
                }

                #if DEBUG
                Section("Debug") {
                    Toggle("Allow cellular model downloads", isOn: $cellularBypass)
                        .onChange(of: cellularBypass) { _, enabled in
                            Task { await downloads.setCellularBypass(enabled) }
                        }
                }
                #endif
            }
            .navigationTitle("Models")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await downloads.refreshStorageUsage() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                    .accessibilityLabel("Refresh storage")
                }
            }
            .alert("Not Enough Storage", isPresented: Binding(
                get: { diskSpaceAlertBytes != nil },
                set: { if !$0 { diskSpaceAlertBytes = nil } }
            )) {
                Button("OK", role: .cancel) {}
            } message: {
                if let bytes = diskSpaceAlertBytes {
                    let amount = ByteCountFormatter.string(fromByteCount: Int64(Double(bytes) * 1.1), countStyle: .file)
                    Text("This model needs about \(amount) free before download.")
                }
            }
        }
        .task {
            await downloads.refreshStorageUsage()
            packTokenDraft = knowledgePacks.apiToken
            packBaseURLDraft = knowledgePacks.apiBaseURLString
        }
    }

    private var isPackBusy: Bool {
        if case .checking = knowledgePacks.state { return true }
        if case .downloading = knowledgePacks.state { return true }
        return false
    }

    private func savePackSettings() {
        knowledgePacks.saveSettings(token: packTokenDraft, apiBaseURLString: packBaseURLDraft)
    }

    @ViewBuilder
    private var knowledgePackStatusRow: some View {
        switch knowledgePacks.state {
        case .notInstalled:
            Label("No pack installed", systemImage: "tray")
                .foregroundStyle(.secondary)
        case .checking:
            HStack {
                ProgressView()
                Text("Checking pack")
            }
        case .downloading:
            HStack {
                ProgressView()
                Text("Downloading pack")
            }
        case .ready(let version, let docCount, let wikiSectionCount):
            Label("Pack v\(version) - \(docCount) docs - \(wikiSectionCount) wiki pages", systemImage: "checkmark.circle.fill")
                .foregroundStyle(.green)
        case .failed(let message):
            Label(message, systemImage: "exclamationmark.triangle")
                .foregroundStyle(.orange)
        }
    }

    private func start(_ model: CanisModel) {
        Task {
            guard await downloads.hasSufficientSpace(for: model.estimatedBytes) else {
                diskSpaceAlertBytes = model.estimatedBytes
                return
            }
            await downloads.startDownload(model)
        }
    }
}
