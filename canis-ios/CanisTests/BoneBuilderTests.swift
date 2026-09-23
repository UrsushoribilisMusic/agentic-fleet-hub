import SQLite3
import XCTest
@testable import Canis

final class BoneBuilderTests: XCTestCase {
    private let builder = BoneBuilder()

    // MARK: - Helpers

    private func makeChunks(_ items: [(text: String, page: Int)]) -> [BoneChunk] {
        items.enumerated().map { i, pair in
            BoneChunk(index: i, text: pair.text, sourcePage: pair.page)
        }
    }

    /// Opens a read-only connection to a bone file.
    private func openReadOnly(_ url: URL) -> OpaquePointer? {
        var db: OpaquePointer?
        guard sqlite3_open_v2(url.path, &db, SQLITE_OPEN_READONLY | SQLITE_OPEN_FULLMUTEX, nil) == SQLITE_OK else {
            return nil
        }
        return db
    }

    private func intValue(_ db: OpaquePointer, _ sql: String) -> Int32 {
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK,
              sqlite3_step(stmt) == SQLITE_ROW else { return -1 }
        let v = sqlite3_column_int(stmt, 0)
        sqlite3_finalize(stmt)
        return v
    }

    private func stringRows(_ db: OpaquePointer, _ sql: String) -> [String] {
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK else { return [] }
        var rows: [String] = []
        while sqlite3_step(stmt) == SQLITE_ROW {
            rows.append(sqlite3_column_text(stmt, 0).map { String(cString: $0) } ?? "")
        }
        sqlite3_finalize(stmt)
        return rows
    }

    // MARK: - (a) Schema shape

    func testWrittenBoneHasRequiredTables() throws {
        let url = try builder.build(
            chunks: makeChunks([("hello world", 1)]),
            docTitle: "Test Doc",
            sourceName: "test.txt"
        )
        defer { try? FileManager.default.removeItem(at: url) }

        let db = try XCTUnwrap(openReadOnly(url))
        defer { sqlite3_close(db) }

        for table in ["meta", "chunks", "wiki_sections"] {
            var stmt: OpaquePointer?
            let sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='\(table)'"
            XCTAssertEqual(sqlite3_prepare_v2(db, sql, -1, &stmt, nil), SQLITE_OK)
            XCTAssertEqual(sqlite3_step(stmt), SQLITE_ROW, "Missing table: \(table)")
            sqlite3_finalize(stmt)
        }
    }

    func testIndexesExist() throws {
        let url = try builder.build(
            chunks: makeChunks([("some text", 1)]),
            docTitle: "Index Test",
            sourceName: "idx.txt"
        )
        defer { try? FileManager.default.removeItem(at: url) }

        let db = try XCTUnwrap(openReadOnly(url))
        defer { sqlite3_close(db) }

        let indexes = stringRows(db, "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
        XCTAssertTrue(indexes.contains("idx_chunks_doc"), "Missing idx_chunks_doc")
        XCTAssertTrue(indexes.contains("idx_wiki_doc"),   "Missing idx_wiki_doc")
    }

    // MARK: - (b) Row counts

    func testChunkAndWikiCountsMatchInput() throws {
        let chunks = makeChunks([
            ("First chunk about robots and calibration.", 1),
            ("Second chunk about brushes and canvas.",   2),
            ("Third chunk about color theory.",          3),
        ])
        let url = try builder.build(chunks: chunks, docTitle: "Art Guide", sourceName: "art.pdf")
        defer { try? FileManager.default.removeItem(at: url) }

        let db = try XCTUnwrap(openReadOnly(url))
        defer { sqlite3_close(db) }

        XCTAssertEqual(intValue(db, "SELECT COUNT(*) FROM chunks"),       Int32(chunks.count))
        XCTAssertEqual(intValue(db, "SELECT COUNT(*) FROM wiki_sections"), Int32(chunks.count))
    }

    func testEmptyChunkListProducesValidEmptyBone() throws {
        let url = try builder.build(chunks: [], docTitle: "Empty Doc", sourceName: "empty.txt")
        defer { try? FileManager.default.removeItem(at: url) }

        let db = try XCTUnwrap(openReadOnly(url))
        defer { sqlite3_close(db) }

        XCTAssertEqual(intValue(db, "SELECT COUNT(*) FROM chunks"),       0)
        XCTAssertEqual(intValue(db, "SELECT COUNT(*) FROM wiki_sections"), 0)
    }

    // MARK: - (c) Retriever integration — acceptance criterion

    /// A bone built from sample content must load through KnowledgePackRetriever
    /// and return non-empty hits for a relevant query.
    func testBuiltBoneLoadsViaRetrieverAndReturnsHits() throws {
        let chunks = makeChunks([
            ("The pump calibration window must be exactly 20 minutes for torque drift correction.", 1),
            ("Use the red wrench for tightening bolts during arm joint assembly.",                  2),
            ("The servo motor draws 2.4 amps at peak load under standard operating conditions.",   3),
        ])
        let url = try builder.build(
            chunks: chunks,
            docTitle: "Robot Manual",
            sourceName: "robot-manual.txt"
        )
        defer { try? FileManager.default.removeItem(at: url) }

        let retrieval = try KnowledgePackRetriever(packURL: url)
            .retrieve(question: "What is the pump calibration window for torque drift?")

        XCTAssertFalse(retrieval.hits.isEmpty, "Expected at least one hit from the built bone")
        XCTAssertTrue(
            retrieval.hits[0].body.contains("calibration") || retrieval.hits[0].body.contains("pump"),
            "Top hit should mention calibration or pump; got: \(retrieval.hits[0].body)"
        )
    }

    func testUnrelatedQueryReturnsNoHits() throws {
        let chunks = makeChunks([
            ("The pump calibration window must be exactly 20 minutes for torque drift correction.", 1),
        ])
        let url = try builder.build(
            chunks: chunks,
            docTitle: "Robot Manual",
            sourceName: "manual.txt"
        )
        defer { try? FileManager.default.removeItem(at: url) }

        let retrieval = try KnowledgePackRetriever(packURL: url)
            .retrieve(question: "Who won the football match yesterday?")

        XCTAssertTrue(retrieval.hits.isEmpty)
    }

    // MARK: - (d) ID and title conventions

    func testSectionTitlesFollowPagePattern() throws {
        let chunks = makeChunks([
            ("Content for page one.", 1),
            ("Content for page two.", 2),
        ])
        let url = try builder.build(chunks: chunks, docTitle: "My Doc", sourceName: "doc.txt")
        defer { try? FileManager.default.removeItem(at: url) }

        let db = try XCTUnwrap(openReadOnly(url))
        defer { sqlite3_close(db) }

        let titles = stringRows(db, "SELECT title FROM wiki_sections ORDER BY section_index ASC")
        XCTAssertEqual(titles.count, 2)
        XCTAssertEqual(titles[0], "My Doc - p.1")
        XCTAssertEqual(titles[1], "My Doc - p.2")
    }

    func testChunkIdsUseCPrefix() throws {
        let url = try builder.build(
            chunks: makeChunks([("text", 1), ("more text", 2)]),
            docTitle: "ID Test",
            sourceName: "id.txt"
        )
        defer { try? FileManager.default.removeItem(at: url) }

        let db = try XCTUnwrap(openReadOnly(url))
        defer { sqlite3_close(db) }

        let ids = stringRows(db, "SELECT id FROM chunks ORDER BY chunk_index ASC")
        XCTAssertTrue(ids[0].hasPrefix("c-"),  "chunks.id should start with 'c-'; got \(ids[0])")
        XCTAssertTrue(ids[0].hasSuffix("-s1"), "First chunk id should end with '-s1'; got \(ids[0])")
        XCTAssertTrue(ids[1].hasSuffix("-s2"), "Second chunk id should end with '-s2'; got \(ids[1])")
    }

    func testWikiSectionIdsDoNotUseCPrefix() throws {
        let url = try builder.build(
            chunks: makeChunks([("text", 1)]),
            docTitle: "Wiki ID Test",
            sourceName: "w.txt"
        )
        defer { try? FileManager.default.removeItem(at: url) }

        let db = try XCTUnwrap(openReadOnly(url))
        defer { sqlite3_close(db) }

        let ids = stringRows(db, "SELECT id FROM wiki_sections")
        XCTAssertFalse(ids[0].hasPrefix("c-"), "wiki_sections.id should NOT start with 'c-'; got \(ids[0])")
        XCTAssertTrue(ids[0].hasSuffix("-s1"), "wiki_sections.id should end with '-s1'; got \(ids[0])")
    }

    func testDocIdIsEmbeddedInRowIds() throws {
        let url = try builder.build(
            chunks: makeChunks([("text", 1)]),
            docTitle: "Hello World",
            sourceName: "hw.txt"
        )
        defer { try? FileManager.default.removeItem(at: url) }

        let db = try XCTUnwrap(openReadOnly(url))
        defer { sqlite3_close(db) }

        let chunkIds = stringRows(db, "SELECT id FROM chunks")
        let wikiIds  = stringRows(db, "SELECT id FROM wiki_sections")

        XCTAssertTrue(chunkIds[0].contains("hello-world"),
                      "chunks.id should embed docId 'hello-world'; got \(chunkIds[0])")
        XCTAssertTrue(wikiIds[0].contains("hello-world"),
                      "wiki_sections.id should embed docId 'hello-world'; got \(wikiIds[0])")
    }

    // MARK: - (e) Source page

    func testSourcePageStoredAsPageNumber() throws {
        let url = try builder.build(
            chunks: makeChunks([("Page 5 content.", 5)]),
            docTitle: "PDF Doc",
            sourceName: "doc.pdf"
        )
        defer { try? FileManager.default.removeItem(at: url) }

        let db = try XCTUnwrap(openReadOnly(url))
        defer { sqlite3_close(db) }

        let pages = stringRows(db, "SELECT source_page FROM chunks")
        XCTAssertEqual(pages.first, "5", "source_page should be the string page number")
    }

    // MARK: - (f) Meta rows

    func testMetaContainsRequiredKeys() throws {
        let chunks = makeChunks([("a", 1), ("b", 2)])
        let url = try builder.build(chunks: chunks, docTitle: "Meta Test", sourceName: "m.txt")
        defer { try? FileManager.default.removeItem(at: url) }

        let db = try XCTUnwrap(openReadOnly(url))
        defer { sqlite3_close(db) }

        let keys = Set(stringRows(db, "SELECT key FROM meta"))
        for required in ["version", "user_id", "created_at", "doc_count", "chunk_count", "wiki_count"] {
            XCTAssertTrue(keys.contains(required), "meta missing key: \(required)")
        }

        let chunkCount = stringRows(db, "SELECT value FROM meta WHERE key='chunk_count'").first
        XCTAssertEqual(chunkCount, "2")
    }

    // MARK: - (g) Reproducibility (content, not timestamps)

    func testIdenticalInputsProduceSameRowContent() throws {
        let chunks = makeChunks([
            ("Reproducibility test content one.", 1),
            ("Second chunk for verification.",    1),
        ])

        let url1 = try builder.build(chunks: chunks, docTitle: "RepTest", sourceName: "rep.txt")
        let url2 = try builder.build(chunks: chunks, docTitle: "RepTest", sourceName: "rep.txt")
        defer {
            try? FileManager.default.removeItem(at: url1)
            try? FileManager.default.removeItem(at: url2)
        }

        let db1 = try XCTUnwrap(openReadOnly(url1))
        let db2 = try XCTUnwrap(openReadOnly(url2))
        defer { sqlite3_close(db1); sqlite3_close(db2) }

        for (table, col) in [("chunks", "text"), ("wiki_sections", "body")] {
            let rows1 = stringRows(db1, "SELECT \(col) FROM \(table) ORDER BY rowid")
            let rows2 = stringRows(db2, "SELECT \(col) FROM \(table) ORDER BY rowid")
            XCTAssertEqual(rows1, rows2, "Mismatch in \(table).\(col)")
        }
    }

    // MARK: - (h) makeDocId helper

    func testMakeDocIdSlugifiesTitle() {
        XCTAssertEqual(BoneBuilder.makeDocId(from: "Robot Ross ATF"), "robot-ross-atf")
        XCTAssertEqual(BoneBuilder.makeDocId(from: "My PDF Document!"), "my-pdf-document")
        XCTAssertEqual(BoneBuilder.makeDocId(from: ""), "untitled")
        XCTAssertEqual(BoneBuilder.makeDocId(from: "   "), "untitled")
    }
}
