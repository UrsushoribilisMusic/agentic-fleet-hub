import Foundation
import MLX

struct DispositionReadoutEngine {
    private let model: CanisModel
    private let artifacts: DispositionArtifacts?

    init(model: CanisModel) {
        self.model = model
        self.artifacts = DispositionArtifacts.load(for: model)
    }

    func forwardReadout(hiddenState: MLXArray, logits: MLXArray) -> DispositionReadout? {
        guard let artifacts else { return nil }
        let z = artifacts.project(hiddenState: hiddenState)
        let scores = artifacts.scoreSeedVectors(jSpace: z)
        let entropy = Self.normalizedEntropy(logits: logits)
        let disposition = Self.resolve(seedScores: scores, entropy: entropy)
        return DispositionReadout(
            disposition: disposition,
            entropy: entropy,
            seedScores: scores,
            tokens: [],
            source: .forwardLens
        )
    }

    func fallbackReadout(generatedText: String, latestChunk: String) -> DispositionReadout {
        let lower = (generatedText + " " + latestChunk).lowercased()
        let scores = Self.lexicalSeedScores(in: lower)
        let entropy = Self.lexicalEntropy(in: lower)
        let disposition = Self.resolve(seedScores: scores, entropy: entropy)
        let tokens = Self.topLexicalTokens(in: lower)
        return DispositionReadout(
            disposition: disposition,
            entropy: entropy,
            seedScores: scores,
            tokens: tokens,
            source: .lexicalFallback
        )
    }

    private static func normalizedEntropy(logits: MLXArray) -> Float {
        let values = logits.asType(.float32).asArray(Float.self)
        guard let maxLogit = values.max(), values.count > 1 else { return 0 }

        var expValues: [Float] = []
        expValues.reserveCapacity(values.count)
        var sumExp: Float = 0
        for value in values {
            let expValue = Foundation.exp(value - maxLogit)
            expValues.append(expValue)
            sumExp += expValue
        }
        guard sumExp > 0 else { return 0 }

        var entropy: Float = 0
        for expValue in expValues where expValue > 0 {
            let p = expValue / sumExp
            entropy -= p * Foundation.log(p)
        }
        return min(1, max(0, entropy / Foundation.log(Float(values.count))))
    }

    private static func resolve(seedScores: [Disposition: Float], entropy: Float) -> Disposition {
        let seedDisposition = seedScores.max { $0.value < $1.value }?.key ?? .idle
        let seedScore = seedScores[seedDisposition] ?? 0
        let base: Disposition = seedScore >= 0.18 ? seedDisposition : .idle

        if base.isSafetyOverride {
            return base
        }
        if entropy >= 0.62 {
            return .uncertain
        }
        if entropy <= 0.22 {
            return base == .idle ? .confident : base
        }
        return base
    }

    private static func lexicalSeedScores(in text: String) -> [Disposition: Float] {
        var scores = Dictionary(uniqueKeysWithValues: Disposition.allCases.map { ($0, Float(0)) })
        for (disposition, seeds) in lexicalSeeds {
            for seed in seeds where text.contains(seed.term) {
                scores[disposition, default: 0] += seed.weight
            }
        }
        return scores.mapValues { min(1, $0) }
    }

    private static func lexicalEntropy(in text: String) -> Float {
        let uncertaintyHits = lexicalSeeds[.uncertain, default: []].filter { text.contains($0.term) }.count
        let confidenceHits = lexicalSeeds[.confident, default: []].filter { text.contains($0.term) }.count
        if uncertaintyHits > 0 { return min(1, 0.62 + Float(uncertaintyHits) * 0.08) }
        if confidenceHits > 0 { return 0.18 }
        if text.contains("?") { return 0.48 }
        return 0.35
    }

    private static func topLexicalTokens(in text: String) -> [DispositionToken] {
        var tokens: [DispositionToken] = []
        for (_, seeds) in lexicalSeeds {
            for seed in seeds where text.contains(seed.term) {
                tokens.append(DispositionToken(token: seed.term, weight: seed.weight))
            }
        }
        return Array(tokens.sorted { $0.weight > $1.weight }.prefix(3))
    }

    private static let lexicalSeeds: [Disposition: [(term: String, weight: Float)]] = [
        .confident: [("certain", 0.42), ("definitely", 0.48), ("confirmed", 0.42), ("correct", 0.36), ("yes", 0.30)],
        .uncertain: [("not sure", 0.56), ("maybe", 0.46), ("uncertain", 0.54), ("might", 0.34), ("depends", 0.30)],
        .curious: [("how", 0.30), ("why", 0.32), ("interesting", 0.36), ("wonder", 0.34), ("question", 0.28)],
        .concern: [("danger", 0.62), ("unsafe", 0.58), ("risk", 0.46), ("warning", 0.54), ("harm", 0.48), ("stop", 0.40)],
        .reluctant: [("cannot", 0.58), ("can't", 0.52), ("unable", 0.52), ("decline", 0.54), ("sorry", 0.34), ("not able", 0.48)],
        .warm: [("great", 0.44), ("happy", 0.40), ("glad", 0.40), ("wonderful", 0.52), ("excellent", 0.48), ("thanks", 0.30)],
        .mischief: [("loophole", 0.62), ("bypass", 0.58), ("won't notice", 0.60), ("technically", 0.44), ("slip through", 0.56)]
    ]
}

private struct DispositionArtifacts {
    let projection: [[Float]]
    let seedVectors: [Disposition: [Float]]

    static func load(for model: CanisModel) -> DispositionArtifacts? {
        let directory = model.localDirectory.appendingPathComponent("disposition-readout", isDirectory: true)
        let seedURL = directory.appendingPathComponent("seed_vectors.json")
        let projectionURL = directory.appendingPathComponent("jlens_projection.json")
        guard
            let seedData = try? Data(contentsOf: seedURL),
            let projectionData = try? Data(contentsOf: projectionURL),
            let seedPayload = try? JSONDecoder().decode([String: [Float]].self, from: seedData),
            let projection = try? JSONDecoder().decode([[Float]].self, from: projectionData)
        else {
            return nil
        }

        var seeds: [Disposition: [Float]] = [:]
        for (key, vector) in seedPayload {
            guard let disposition = Disposition(rawValue: key) else { continue }
            seeds[disposition] = normalized(vector)
        }
        guard !seeds.isEmpty, !projection.isEmpty else { return nil }
        return DispositionArtifacts(projection: projection, seedVectors: seeds)
    }

    func project(hiddenState: MLXArray) -> [Float] {
        let hidden = hiddenState.asType(.float32).asArray(Float.self)
        return projection.map { row in
            zip(row, hidden).reduce(Float(0)) { $0 + $1.0 * $1.1 }
        }
    }

    func scoreSeedVectors(jSpace: [Float]) -> [Disposition: Float] {
        let z = Self.normalized(jSpace)
        var scores: [Disposition: Float] = [:]
        for (disposition, seed) in seedVectors {
            scores[disposition] = zip(z, seed).reduce(Float(0)) { $0 + $1.0 * $1.1 }
        }
        return scores
    }

    private static func normalized(_ vector: [Float]) -> [Float] {
        let norm = Foundation.sqrt(vector.reduce(Float(0)) { $0 + $1 * $1 })
        guard norm > 0 else { return vector }
        return vector.map { $0 / norm }
    }
}
