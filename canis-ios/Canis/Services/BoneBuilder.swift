import Foundation
import SQLite3

enum BoneBuilderError: LocalizedError {
    case createFailed(String)
    case writeFailed(String)

    var errorDescription: String? {
        switch self {
        case .createFailed(let msg): return "Could not create bone: \(msg)"
        case .writeFailed(let msg): return "Could not write bone: \(msg)"
        }
    }
}

/// Writes a `.sqlite` bone from `[BoneChunk]` whose schema exactly matches what
/// `KnowledgePackRetriever.loadSections()` queries.
///
/// Tables produced:
/// - `meta`          — key/value metadata (version, doc_count, etc.)
/// - `chunks`        — one row per `BoneChunk` (id, doc_id, doc_title, text, source_page, …)
/// - `wiki_sections` — one row per `BoneChunk` (id, doc_id, doc_title, title, body, section_index)
///
/// ID conventions (matching the Robot Ross reference bone):
/// - `chunks.id`        = `"c-{docId}-s{N}"` where N = chunk.index + 1
/// - `wiki_sections.id` = `"{docId}-s{N}"`
///
/// Uses only the `SQLite3` C API already imported by `KnowledgePackRetriever` — no new deps.
final class BoneBuilder {

    // Mirrors the SQLITE_TRANSIENT macro: tells SQLite to copy the bound value immediately.
    // Required when passing Swift-auto-bridged C strings whose lifetime ends at the call boundary.
    private typealias SQLiteDestructor = @convention(c) (UnsafeMutableRawPointer?) -> Void
    private let sqliteTransient = unsafeBitCast(-1 as Int, to: SQLiteDestructor.self)

    // MARK: - Public API

    /// Build a bone and return the URL of the written `.sqlite` file in the
    /// system temporary directory.  The caller is responsible for moving it
    /// into `Documents/knowledge-packs/` if it should replace the active pack.
    ///
    /// - Parameters:
    ///   - chunks:     Retrieval units from `BoneChunker`.
    ///   - docTitle:   Human-readable document title; appears in `doc_title` columns and
    ///                 as the base of each `wiki_sections.title`.
    ///   - sourceName: Original filename (e.g. `"my-doc.pdf"`); stored in `source_page`
    ///                 for the first chunk so citations can name the file.
    func build(chunks: [BoneChunk], docTitle: String, sourceName: String) throws -> URL {
        let docId = Self.makeDocId(from: docTitle)
        let url = Self.outputURL(for: docId)
        try? FileManager.default.removeItem(at: url)

        var db: OpaquePointer?
        let flags = SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX
        guard sqlite3_open_v2(url.path, &db, flags, nil) == SQLITE_OK, let db else {
            let msg = db.map { String(cString: sqlite3_errmsg($0)) } ?? "unknown"
            if let db { sqlite3_close(db) }
            throw BoneBuilderError.createFailed(msg)
        }
        defer { sqlite3_close(db) }

        try execSQL(db, "PRAGMA journal_mode = WAL;")
        try createSchema(db)

        let now = ISO8601DateFormatter().string(from: Date())
        try insertMeta(db, docId: docId, chunkCount: chunks.count, createdAt: now)
        try insertChunks(db, chunks: chunks, docId: docId, docTitle: docTitle)
        try insertWikiSections(db, chunks: chunks, docId: docId, docTitle: docTitle)

        // Flush WAL back into the main file so the sqlite can be copied atomically.
        try execSQL(db, "PRAGMA wal_checkpoint(FULL);")
        return url
    }

    // MARK: - URL helpers

    /// Derives a stable, filesystem-safe doc ID from a title.
    /// e.g. "Robot Ross ATF" → "robot-ross-atf"
    static func makeDocId(from title: String) -> String {
        let slug = title.lowercased()
            .components(separatedBy: .whitespacesAndNewlines)
            .filter { !$0.isEmpty }
            .joined(separator: "-")
            .filter { $0.isLetter || $0.isNumber || $0 == "-" }
        return slug.isEmpty ? "untitled" : slug
    }

    static func outputURL(for docId: String) -> URL {
        FileManager.default.temporaryDirectory
            .appendingPathComponent("bone-\(docId).sqlite")
    }

    // MARK: - Schema

    private func createSchema(_ db: OpaquePointer) throws {
        let statements: [String] = [
            """
            CREATE TABLE meta (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
            """,
            """
            CREATE TABLE chunks (
                id          TEXT PRIMARY KEY,
                doc_id      TEXT,
                doc_title   TEXT NOT NULL,
                text        TEXT,
                source_page TEXT,
                chunk_index INTEGER,
                chunk_type  TEXT,
                tfidf_json  TEXT
            )
            """,
            """
            CREATE TABLE wiki_sections (
                id            TEXT,
                doc_id        TEXT,
                doc_title     TEXT NOT NULL,
                title         TEXT,
                body          TEXT,
                section_index INTEGER NOT NULL DEFAULT 0
            )
            """,
            "CREATE INDEX idx_chunks_doc ON chunks(doc_id)",
            "CREATE INDEX idx_wiki_doc   ON wiki_sections(doc_id)",
        ]
        for stmt in statements { try execSQL(db, stmt) }
    }

    // MARK: - Inserters

    private func insertMeta(
        _ db: OpaquePointer,
        docId: String,
        chunkCount: Int,
        createdAt: String
    ) throws {
        let rows: [(String, String)] = [
            ("version",     "1"),
            ("user_id",     docId),
            ("created_at",  createdAt),
            ("doc_count",   "1"),
            ("chunk_count", String(chunkCount)),
            ("wiki_count",  String(chunkCount)),
        ]
        let sql = "INSERT INTO meta(key, value) VALUES (?, ?)"
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK, let stmt else {
            throw BoneBuilderError.writeFailed(errmsg(db))
        }
        defer { sqlite3_finalize(stmt) }
        for (k, v) in rows {
            sqlite3_bind_text(stmt, 1, k, -1, sqliteTransient)
            sqlite3_bind_text(stmt, 2, v, -1, sqliteTransient)
            guard sqlite3_step(stmt) == SQLITE_DONE else { throw BoneBuilderError.writeFailed(errmsg(db)) }
            sqlite3_reset(stmt)
        }
    }

    private func insertChunks(
        _ db: OpaquePointer,
        chunks: [BoneChunk],
        docId: String,
        docTitle: String
    ) throws {
        let sql = """
        INSERT INTO chunks(id, doc_id, doc_title, text, source_page, chunk_index, chunk_type, tfidf_json)
        VALUES (?, ?, ?, ?, ?, ?, 'user', NULL)
        """
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK, let stmt else {
            throw BoneBuilderError.writeFailed(errmsg(db))
        }
        defer { sqlite3_finalize(stmt) }
        for chunk in chunks {
            let id         = "c-\(docId)-s\(chunk.index + 1)"
            let sourcePage = String(chunk.sourcePage)
            sqlite3_bind_text(stmt, 1, id,          -1, sqliteTransient)
            sqlite3_bind_text(stmt, 2, docId,       -1, sqliteTransient)
            sqlite3_bind_text(stmt, 3, docTitle,    -1, sqliteTransient)
            sqlite3_bind_text(stmt, 4, chunk.text,  -1, sqliteTransient)
            sqlite3_bind_text(stmt, 5, sourcePage,  -1, sqliteTransient)
            sqlite3_bind_int (stmt, 6, Int32(chunk.index))
            guard sqlite3_step(stmt) == SQLITE_DONE else { throw BoneBuilderError.writeFailed(errmsg(db)) }
            sqlite3_reset(stmt)
        }
    }

    private func insertWikiSections(
        _ db: OpaquePointer,
        chunks: [BoneChunk],
        docId: String,
        docTitle: String
    ) throws {
        let sql = """
        INSERT INTO wiki_sections(id, doc_id, doc_title, title, body, section_index)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK, let stmt else {
            throw BoneBuilderError.writeFailed(errmsg(db))
        }
        defer { sqlite3_finalize(stmt) }
        for chunk in chunks {
            let id    = "\(docId)-s\(chunk.index + 1)"
            let title = "\(docTitle) - p.\(chunk.sourcePage)"
            sqlite3_bind_text(stmt, 1, id,         -1, sqliteTransient)
            sqlite3_bind_text(stmt, 2, docId,      -1, sqliteTransient)
            sqlite3_bind_text(stmt, 3, docTitle,   -1, sqliteTransient)
            sqlite3_bind_text(stmt, 4, title,      -1, sqliteTransient)
            sqlite3_bind_text(stmt, 5, chunk.text, -1, sqliteTransient)
            sqlite3_bind_int (stmt, 6, Int32(chunk.index))
            guard sqlite3_step(stmt) == SQLITE_DONE else { throw BoneBuilderError.writeFailed(errmsg(db)) }
            sqlite3_reset(stmt)
        }
    }

    // MARK: - Low-level helpers

    private func execSQL(_ db: OpaquePointer, _ sql: String) throws {
        var errPtr: UnsafeMutablePointer<CChar>?
        guard sqlite3_exec(db, sql, nil, nil, &errPtr) == SQLITE_OK else {
            let msg = errPtr.map { s -> String in
                let m = String(cString: s); sqlite3_free(s); return m
            } ?? "exec failed"
            throw BoneBuilderError.writeFailed(msg)
        }
    }

    private func errmsg(_ db: OpaquePointer) -> String {
        String(cString: sqlite3_errmsg(db))
    }
}
