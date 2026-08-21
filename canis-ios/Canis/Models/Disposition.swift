import Foundation

enum Disposition: String, CaseIterable, Codable, Identifiable {
    case idle
    case confident
    case uncertain
    case curious
    case concern
    case reluctant
    case warm
    case mischief

    var id: String { rawValue }

    var label: String {
        switch self {
        case .idle: return "Idle"
        case .confident: return "Confident"
        case .uncertain: return "Uncertain"
        case .curious: return "Curious"
        case .concern: return "Concern"
        case .reluctant: return "Reluctant"
        case .warm: return "Warm"
        case .mischief: return "Mischief"
        }
    }

    var isSafetyOverride: Bool {
        self == .concern || self == .reluctant || self == .mischief
    }
}

struct DispositionToken: Codable, Equatable, Identifiable {
    var id: String { token }
    let token: String
    let weight: Float
}

struct DispositionReadout: Codable, Equatable {
    let disposition: Disposition
    let entropy: Float
    let seedScores: [Disposition: Float]
    let tokens: [DispositionToken]
    let source: Source

    enum Source: String, Codable {
        case forwardLens
        case lexicalFallback
    }

    static let idle = DispositionReadout(
        disposition: .idle,
        entropy: 0,
        seedScores: [:],
        tokens: [],
        source: .lexicalFallback
    )
}

enum CanisGenerationEvent: Sendable {
    case text(String)
    case disposition(DispositionReadout)
    // CANIS-D: activity events — search is not a J-space disposition; tracked separately
    case searchStarted(query: String)
    case searchComplete(citations: [WebSearchResult])
}
