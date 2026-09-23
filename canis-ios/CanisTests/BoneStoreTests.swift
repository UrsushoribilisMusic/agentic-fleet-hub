import XCTest
@testable import Canis

@MainActor
final class BoneStoreTests: XCTestCase {
    private let store = KnowledgePackStore.shared
    private let builder = BoneBuilder()

    override func setUp() async throws {
        // Ensure the store is initialised with fresh disk state.
        store.setup()
    }

    // MARK: - BoneEntry codable

    func testBoneEntryRoundTrips() throws {
        let entry = BoneEntry(
            id: "test-uuid-abc",
            name: "My Test Bone",
            docCount: 5,
            wikiSectionCount: 42,
            size: 102_400,
            createdAt: Date(timeIntervalSince1970: 1_700_000_000),
            isActive: true,
            isBuiltIn: false
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let data = try encoder.encode(entry)
        let decoded = try decoder.decode(BoneEntry.self, from: data)

        XCTAssertEqual(decoded.id,               entry.id)
        XCTAssertEqual(decoded.name,             entry.name)
        XCTAssertEqual(decoded.docCount,         entry.docCount)
        XCTAssertEqual(decoded.wikiSectionCount, entry.wikiSectionCount)
        XCTAssertEqual(decoded.size,             entry.size)
        XCTAssertEqual(decoded.isActive,         entry.isActive)
        XCTAssertEqual(decoded.isBuiltIn,        entry.isBuiltIn)
    }

    func testBoneEntryArrayRoundTrips() throws {
        let entries: [BoneEntry] = [
            BoneEntry(id: "a", name: "A", docCount: 1, wikiSectionCount: 2, size: 100,
                      createdAt: Date(), isActive: true,  isBuiltIn: true),
            BoneEntry(id: "b", name: "B", docCount: 3, wikiSectionCount: 4, size: 200,
                      createdAt: Date(), isActive: false, isBuiltIn: false),
        ]
        let encoder = JSONEncoder(); encoder.dateEncodingStrategy = .iso8601
        let decoder = JSONDecoder(); decoder.dateDecodingStrategy = .iso8601

        let decoded = try decoder.decode([BoneEntry].self, from: encoder.encode(entries))

        XCTAssertEqual(decoded.count, 2)
        XCTAssertEqual(decoded[0].id, "a")
        XCTAssertTrue(decoded[0].isActive)
        XCTAssertEqual(decoded[1].id, "b")
        XCTAssertFalse(decoded[1].isActive)
    }

    // MARK: - URL helpers

    func testCurrentPackURLIsLegacyPath() {
        XCTAssertEqual(KnowledgePackStore.currentPackURL.lastPathComponent, "current.sqlite")
    }

    func testBonesDirectoryIsInsideKnowledgePacks() {
        let bones = KnowledgePackStore.bonesDirectoryURL
        XCTAssertTrue(bones.path.contains("knowledge-packs/bones"))
    }

    // MARK: - Built-in seeding

    func testBuiltInRobotRossBoneIsPresentAfterSetup() {
        XCTAssertTrue(
            store.bones.contains { $0.id == KnowledgePackStore.builtinRobotRossID },
            "Robot Ross built-in bone must be in the index after setup()"
        )
    }

    func testBuiltInBoneCannotBeDeleted() throws {
        let countBefore = store.bones.count
        try store.deleteBone(id: KnowledgePackStore.builtinRobotRossID)
        XCTAssertEqual(store.bones.count, countBefore,
                       "Built-in bone must not be deletable")
    }

    // MARK: - Install / rename / delete

    func testInstallRenameDelete() async throws {
        let initialCount = store.bones.count

        let url = try builder.build(
            chunks: [BoneChunk(index: 0, text: "Alpha bone test content.", sourcePage: 1)],
            docTitle: "Alpha Bone",
            sourceName: "alpha.txt"
        )
        let entry = try store.installBone(from: url, name: "Alpha", docCount: 1, wikiSectionCount: 1)
        XCTAssertEqual(store.bones.count, initialCount + 1)
        XCTAssertTrue(store.bones.contains { $0.id == entry.id })

        // Rename
        try store.renameBone(id: entry.id, name: "Alpha Renamed")
        XCTAssertEqual(store.bones.first { $0.id == entry.id }?.name, "Alpha Renamed")

        // Delete
        try store.deleteBone(id: entry.id)
        XCTAssertFalse(store.bones.contains { $0.id == entry.id })
        XCTAssertEqual(store.bones.count, initialCount)
    }

    // MARK: - Multiple bones coexist

    func testMultipleBonesCoexist() async throws {
        var installedIDs: [String] = []
        for i in 1...3 {
            let url = try builder.build(
                chunks: [BoneChunk(index: 0, text: "Bone \(i) unique content.", sourcePage: 1)],
                docTitle: "Coexist Bone \(i)",
                sourceName: "bone\(i).txt"
            )
            let e = try store.installBone(from: url, name: "Coexist \(i)", docCount: 1, wikiSectionCount: 1)
            installedIDs.append(e.id)
        }
        defer {
            installedIDs.forEach { try? store.deleteBone(id: $0) }
        }

        for id in installedIDs {
            XCTAssertTrue(store.bones.contains { $0.id == id },
                          "Bone \(id) should be in the index")
        }
        // Exactly one bone should be active at any time
        XCTAssertEqual(store.bones.filter { $0.isActive }.count, 1)
    }

    // MARK: - setActiveBone changes activePackURL

    func testSetActiveBoneChangesActivePackURL() async throws {
        let url1 = try builder.build(
            chunks: [BoneChunk(index: 0, text: "Robots and painting.", sourcePage: 1)],
            docTitle: "Bone One", sourceName: "one.txt"
        )
        let url2 = try builder.build(
            chunks: [BoneChunk(index: 0, text: "Quantum mechanics and physics.", sourcePage: 1)],
            docTitle: "Bone Two", sourceName: "two.txt"
        )
        let bone1 = try store.installBone(from: url1, name: "Bone One", docCount: 1, wikiSectionCount: 1)
        let bone2 = try store.installBone(from: url2, name: "Bone Two", docCount: 1, wikiSectionCount: 1)
        defer {
            try? store.deleteBone(id: bone1.id)
            try? store.deleteBone(id: bone2.id)
        }

        try store.setActiveBone(id: bone1.id)
        XCTAssertEqual(KnowledgePackStore.activePackURL.lastPathComponent, "\(bone1.id).sqlite")

        try store.setActiveBone(id: bone2.id)
        XCTAssertEqual(KnowledgePackStore.activePackURL.lastPathComponent, "\(bone2.id).sqlite")
    }

    // MARK: - Switching active bone changes retrieval results

    func testSwitchingActiveBoneChangesRetrieval() async throws {
        let url1 = try builder.build(
            chunks: [BoneChunk(index: 0, text: "Robots painting canvases with brushes.", sourcePage: 1)],
            docTitle: "Robots Doc", sourceName: "robots.txt"
        )
        let url2 = try builder.build(
            chunks: [BoneChunk(index: 0, text: "Quantum entanglement and superposition.", sourcePage: 1)],
            docTitle: "Quantum Doc", sourceName: "quantum.txt"
        )
        let bone1 = try store.installBone(from: url1, name: "Robots", docCount: 1, wikiSectionCount: 1)
        let bone2 = try store.installBone(from: url2, name: "Quantum", docCount: 1, wikiSectionCount: 1)
        defer {
            try? store.deleteBone(id: bone1.id)
            try? store.deleteBone(id: bone2.id)
        }

        try store.setActiveBone(id: bone1.id)
        let hits1 = try KnowledgePackRetriever().retrieve(question: "robots painting").hits
        XCTAssertFalse(hits1.isEmpty, "bone1 (robots) should return hits for 'robots painting'")
        XCTAssertTrue(hits1.allSatisfy { $0.docTitle == "Robots Doc" })

        try store.setActiveBone(id: bone2.id)
        let hits2 = try KnowledgePackRetriever().retrieve(question: "quantum entanglement").hits
        XCTAssertFalse(hits2.isEmpty, "bone2 (quantum) should return hits for 'quantum entanglement'")
        XCTAssertTrue(hits2.allSatisfy { $0.docTitle == "Quantum Doc" })
    }

    // MARK: - Delete active bone re-activates built-in

    func testDeleteActiveBoneReactivatesBuiltIn() async throws {
        let url = try builder.build(
            chunks: [BoneChunk(index: 0, text: "Temporary bone content.", sourcePage: 1)],
            docTitle: "Temp",
            sourceName: "temp.txt"
        )
        let entry = try store.installBone(from: url, name: "Temp", docCount: 1, wikiSectionCount: 1)
        try store.setActiveBone(id: entry.id)

        XCTAssertTrue(store.bones.first { $0.id == entry.id }?.isActive == true)

        try store.deleteBone(id: entry.id)

        // After deletion the built-in should be active again
        let builtin = store.bones.first { $0.id == KnowledgePackStore.builtinRobotRossID }
        XCTAssertTrue(builtin?.isActive == true,
                      "Built-in Robot Ross bone must become active after user bone is deleted")
        XCTAssertEqual(store.bones.filter { $0.isActive }.count, 1)
    }
}
