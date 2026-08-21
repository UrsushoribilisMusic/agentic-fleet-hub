import SwiftUI

struct MessageBubbleView: View {
    let message: ChatMessage

    private var isUser: Bool { message.role == .user }

    var body: some View {
        HStack {
            if isUser { Spacer(minLength: 44) }
            VStack(alignment: .leading, spacing: 6) {
                Text(message.content.isEmpty && message.isStreaming ? "Thinking..." : message.content)
                    .font(.body)
                    .textSelection(.enabled)
                if let modelID = message.modelID, let model = CanisModel(rawValue: modelID), !isUser {
                    Text(model.displayName)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                if let readout = message.dispositionReadout, !isUser {
                    HStack(spacing: 6) {
                        Text(readout.disposition.label)
                        Text("H \(readout.entropy, specifier: "%.2f")")
                    }
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                }
                // CANIS-D: citation list — shown when the model did a web search
                if !message.citations.isEmpty, !isUser {
                    Divider()
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Sources")
                            .font(.caption2)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)
                        ForEach(Array(message.citations.enumerated()), id: \.element.id) { index, citation in
                            HStack(alignment: .top, spacing: 4) {
                                Text("[\(index + 1)]")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                                    .frame(width: 20, alignment: .leading)
                                VStack(alignment: .leading, spacing: 1) {
                                    Text(citation.title)
                                        .font(.caption2)
                                        .fontWeight(.medium)
                                        .lineLimit(1)
                                    Text(citation.displayURL)
                                        .font(.caption2)
                                        .foregroundStyle(.blue)
                                        .lineLimit(1)
                                }
                            }
                        }
                    }
                    .padding(.top, 2)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(isUser ? Color.accentColor : Color(.secondarySystemGroupedBackground))
            .foregroundStyle(isUser ? .white : .primary)
            .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
            if !isUser { Spacer(minLength: 44) }
        }
    }
}
