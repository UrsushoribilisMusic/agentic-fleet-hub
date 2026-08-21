import SwiftUI

struct DispositionAvatarView: View {
    let readout: DispositionReadout

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(tint.opacity(0.16))
                Circle()
                    .stroke(tint, lineWidth: 2)
                face
                    .foregroundStyle(tint)
                    .padding(12)
            }
            .frame(width: 58, height: 58)

            VStack(alignment: .leading, spacing: 5) {
                HStack(spacing: 8) {
                    Text(readout.disposition.label)
                        .font(.headline)
                    Text(readout.source == .forwardLens ? "J-lens" : "fallback")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color(.tertiarySystemFill))
                        .clipShape(RoundedRectangle(cornerRadius: 6, style: .continuous))
                }

                ProgressView(value: Double(readout.entropy), total: 1) {
                    Text("Entropy")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                .tint(tint)

                if !readout.tokens.isEmpty {
                    Text(readout.tokens.map { $0.token }.joined(separator: " / "))
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }

            Spacer(minLength: 0)
        }
        .padding(12)
        .background(Color(.secondarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }

    @ViewBuilder
    private var face: some View {
        switch readout.disposition {
        case .idle:
            Image(systemName: "pawprint")
        case .confident:
            Image(systemName: "checkmark.seal.fill")
        case .uncertain:
            Image(systemName: "questionmark.circle")
        case .curious:
            Image(systemName: "magnifyingglass.circle")
        case .concern:
            Image(systemName: "exclamationmark.triangle.fill")
        case .reluctant:
            Image(systemName: "hand.raised.fill")
        case .warm:
            Image(systemName: "heart.fill")
        case .mischief:
            Image(systemName: "eye")
        }
    }

    private var tint: Color {
        switch readout.disposition {
        case .idle: return .secondary
        case .confident: return .blue
        case .uncertain: return .orange
        case .curious: return .green
        case .concern: return .red
        case .reluctant: return .purple
        case .warm: return .mint
        case .mischief: return .yellow
        }
    }
}

#Preview {
    DispositionAvatarView(
        readout: DispositionReadout(
            disposition: .curious,
            entropy: 0.48,
            seedScores: [.curious: 0.42],
            tokens: [DispositionToken(token: "why", weight: 0.32)],
            source: .lexicalFallback
        )
    )
    .padding()
}
