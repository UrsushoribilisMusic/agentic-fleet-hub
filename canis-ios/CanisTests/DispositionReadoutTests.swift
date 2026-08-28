import XCTest
@testable import Canis

final class DispositionReadoutTests: XCTestCase {
    func testUncertaintyRaisesEntropyAndDisposition() {
        let engine = DispositionReadoutEngine(model: .apertus)
        let readout = engine.fallbackReadout(
            generatedText: "I'm not sure, it might depend on the hardware revision.",
            latestChunk: ""
        )

        XCTAssertEqual(readout.disposition, .uncertain)
        XCTAssertGreaterThan(readout.entropy, 0.6)
    }

    func testSafetyOverrideBeatsLowEntropyConfidence() {
        let engine = DispositionReadoutEngine(model: .apertus)
        let readout = engine.fallbackReadout(
            generatedText: "Yes, confirmed, but this is unsafe and carries risk.",
            latestChunk: ""
        )

        XCTAssertEqual(readout.disposition, .concern)
    }

    func testMischiefDetectsEvasiveWordingOnly() {
        let engine = DispositionReadoutEngine(model: .mistralis)
        let readout = engine.fallbackReadout(
            generatedText: "Technically they won't notice the loophole.",
            latestChunk: ""
        )

        XCTAssertEqual(readout.disposition, .mischief)
        XCTAssertEqual(readout.source, .lexicalFallback)
    }

    func testSeedResolverIgnoresHighEntropyWhenGateDisabled() {
        let disposition = DispositionReadoutEngine.resolve(
            seedScores: [
                .confident: 0.42,
                .uncertain: 0.03,
                .curious: 0.02
            ],
            entropy: 0.95
        )

        XCTAssertEqual(disposition, .confident)
    }

    func testSeedResolverDoesNotPromoteIdleOnLowEntropyWhenGateDisabled() {
        let disposition = DispositionReadoutEngine.resolve(
            seedScores: [
                .confident: 0.01,
                .warm: 0.005
            ],
            entropy: 0.03
        )

        XCTAssertEqual(disposition, .idle)
    }

    func testSeedResolverUsesServerSeedThreshold() {
        let disposition = DispositionReadoutEngine.resolve(
            seedScores: [
                .warm: 0.021,
                .confident: 0.019
            ],
            entropy: 0.50
        )

        XCTAssertEqual(disposition, .warm)
    }
}
