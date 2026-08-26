import SQLite3
import XCTest
@testable import Canis

final class KnowledgePackRetrieverTests: XCTestCase {
    func testRetrievalReturnsLocalWikiCitation() throws {
        let packURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("canis-pack-\(UUID().uuidString).sqlite")
        defer { try? FileManager.default.removeItem(at: packURL) }
        try makePack(at: packURL)

        let retrieval = try KnowledgePackRetriever(packURL: packURL)
            .retrieve(question: "What calibration window should I use for torque drift?")

        XCTAssertEqual(retrieval.hits.count, 1)
        XCTAssertEqual(retrieval.hits[0].citationIndex, 1)
        XCTAssertTrue(retrieval.hits[0].citationTitle.contains("Calibration"))
        XCTAssertEqual(retrieval.citations[0].displayURL, "Local wiki page")
        XCTAssertTrue(retrieval.prompt().contains("Source wiki page: Calibration"))
    }

    func testUnrelatedQuestionReturnsNoContext() throws {
        let packURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("canis-pack-\(UUID().uuidString).sqlite")
        defer { try? FileManager.default.removeItem(at: packURL) }
        try makePack(at: packURL)

        let retrieval = try KnowledgePackRetriever(packURL: packURL)
            .retrieve(question: "Who won the football match yesterday?")

        XCTAssertFalse(retrieval.hasContext)
        XCTAssertTrue(retrieval.citations.isEmpty)
    }

    private func makePack(at url: URL) throws {
        var db: OpaquePointer?
        XCTAssertEqual(sqlite3_open(url.path, &db), SQLITE_OK)
        guard let db else { return }
        defer { sqlite3_close(db) }

        let sql = """
        CREATE TABLE chunks (
          id TEXT PRIMARY KEY,
          doc_id TEXT NOT NULL,
          doc_title TEXT NOT NULL,
          text TEXT NOT NULL,
          source_page TEXT NOT NULL DEFAULT '',
          chunk_index INTEGER NOT NULL DEFAULT 0,
          chunk_type TEXT NOT NULL DEFAULT 'document_text',
          tfidf_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE wiki_sections (
          id TEXT PRIMARY KEY,
          doc_id TEXT NOT NULL,
          doc_title TEXT NOT NULL,
          title TEXT NOT NULL,
          body TEXT NOT NULL,
          section_index INTEGER NOT NULL DEFAULT 0,
          chunk_ids TEXT NOT NULL DEFAULT '[]'
        );
        INSERT INTO chunks VALUES (
          'chunk-1',
          'doc-1',
          'Pump Manual',
          'Use the 20 minute torque drift calibration window before field operation.',
          'Calibration',
          0,
          'document_text',
          '{}'
        );
        INSERT INTO wiki_sections VALUES (
          'wiki-1',
          'doc-1',
          'Pump Manual',
          'Calibration',
          'The pump manual requires a 20 minute torque drift calibration window before field operation.',
          0,
          '["chunk-1"]'
        );
        """
        XCTAssertEqual(sqlite3_exec(db, sql, nil, nil, nil), SQLITE_OK)
    }
}
