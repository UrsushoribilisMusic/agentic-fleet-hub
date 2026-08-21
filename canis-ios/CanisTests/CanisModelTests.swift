import XCTest
@testable import Canis

final class CanisModelTests: XCTestCase {
    func testRequiredModelsArePresent() {
        XCTAssertEqual(CanisModel.allCases.map(\.displayName), ["Canis Apertus", "Canis Mistralis"])
    }

    func testManifestsContainConfigAndWeights() {
        for model in CanisModel.allCases {
            let names = Set(model.files.map(\.name))
            XCTAssertTrue(names.contains("config.json"), "\(model.displayName) missing config.json")
            XCTAssertTrue(names.contains("model.safetensors"), "\(model.displayName) missing weights")
            XCTAssertFalse(model.hfRepo.isEmpty)
        }
    }
}
