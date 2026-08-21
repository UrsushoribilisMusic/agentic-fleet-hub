import SwiftUI

struct ModelRowView: View {
    let model: CanisModel
    let state: ModelDownloadState
    let bytesOnDisk: Int64
    let isActive: Bool
    let start: () -> Void
    let resume: () -> Void
    let cancel: () -> Void
    let delete: () -> Void
    let makeActive: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 3) {
                    HStack(spacing: 8) {
                        Text(model.displayName)
                            .font(.headline)
                        if isActive {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(.green)
                        }
                    }
                    Text(model.subtitle)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(storageLine)
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
                Spacer()
                control
            }

            switch state {
            case .downloading(let progress):
                ProgressView(value: progress.fraction)
                Text(progress.displayText)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            case .paused(let reason):
                Label(reason, systemImage: "pause.circle")
                    .font(.caption)
                    .foregroundStyle(.orange)
            case .failed(let message):
                Label(message, systemImage: "exclamationmark.triangle")
                    .font(.caption)
                    .foregroundStyle(.red)
            default:
                EmptyView()
            }
        }
        .padding(.vertical, 6)
    }

    private var storageLine: String {
        let estimated = ByteCountFormatter.string(fromByteCount: model.estimatedBytes, countStyle: .file)
        guard bytesOnDisk > 0 else { return "Estimated \(estimated)" }
        let used = ByteCountFormatter.string(fromByteCount: bytesOnDisk, countStyle: .file)
        return "\(used) on device - estimated \(estimated)"
    }

    @ViewBuilder
    private var control: some View {
        switch state {
        case .notDownloaded:
            Button("Download", action: start)
                .buttonStyle(.borderedProminent)
                .controlSize(.small)
        case .downloading:
            Button("Pause", action: cancel)
                .buttonStyle(.bordered)
                .controlSize(.small)
        case .paused:
            Button("Resume", action: resume)
                .buttonStyle(.borderedProminent)
                .controlSize(.small)
        case .downloaded:
            Menu {
                Button("Use Model", action: makeActive)
                Button("Delete Download", role: .destructive, action: delete)
            } label: {
                Image(systemName: "ellipsis.circle")
                    .font(.title3)
            }
            .accessibilityLabel("Model actions")
        case .failed:
            Button("Retry", action: start)
                .buttonStyle(.bordered)
                .controlSize(.small)
        }
    }
}
