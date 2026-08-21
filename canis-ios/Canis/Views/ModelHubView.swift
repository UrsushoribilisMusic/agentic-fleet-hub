import SwiftUI

struct ModelHubView: View {
    @EnvironmentObject private var downloads: ModelDownloadManager
    @Binding var activeModelID: String
    @State private var diskSpaceAlertBytes: Int64?
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
