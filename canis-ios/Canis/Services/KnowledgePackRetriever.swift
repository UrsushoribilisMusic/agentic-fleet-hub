import Foundation
import SQLite3

struct KnowledgePackHit: Equatable, Sendable {
    let citationIndex: Int
    let sectionID: String
    let title: String
    let body: String
    let docTitle: String
    let sourcePage: String
    let score: Double

    var citationTitle: String {
        docTitle.isEmpty ? title : "\(docTitle): \(title)"
    }

    var citationURL: String {
        "canis://wiki/\(sectionID)"
    }

    var citationSnippet: String {
        KnowledgePackRetriever.excerpt(from: body, around: [])
    }

    func asWebSearchResult() -> WebSearchResult {
        WebSearchResult(
            title: citationTitle,
            url: citationURL,
            snippet: sourcePage.isEmpty ? citationSnippet : "Wiki page: \(sourcePage)",
            bodyExcerpt: citationSnippet
        )
    }
}

struct KnowledgePackRetrieval: Equatable, Sendable {
    let question: String
    let hits: [KnowledgePackHit]

    var citations: [WebSearchResult] {
        hits.map { $0.asWebSearchResult() }
    }

    var hasContext: Bool {
        !hits.isEmpty
    }

    func prompt() -> String {
        guard !hits.isEmpty else { return question }
        let context = hits.map { hit in
            """
            [\(hit.citationIndex)] \(hit.citationTitle)
            Source wiki page: \(hit.sourcePage.isEmpty ? hit.title : hit.sourcePage)
            \(hit.body)
            """
        }.joined(separator: "\n\n")

        return """
        OFFLINE KNOWLEDGE PACK CONTEXT
        Use only these local wiki pages to answer. Cite every factual claim with [1], [2], etc. If the answer is not supported by these wiki pages, say that the downloaded pack does not contain a supporting wiki page.

        \(context)

        QUESTION
        \(question)
        """
    }
}

enum KnowledgePackError: LocalizedError {
    case noDownloadedPack
    case openFailed(String)
    case queryFailed(String)

    var errorDescription: String? {
        switch self {
        case .noDownloadedPack:
            return "No downloaded knowledge pack is installed."
        case .openFailed(let detail):
            return "Could not open the downloaded knowledge pack: \(detail)"
        case .queryFailed(let detail):
            return "Could not read the downloaded knowledge pack: \(detail)"
        }
    }
}

final class KnowledgePackRetriever {
    private struct Section {
        let id: String
        let docTitle: String
        let title: String
        let body: String
        let sourcePage: String
        let text: String
    }

    let packURL: URL

    init(packURL: URL = KnowledgePackStore.currentPackURL) {
        self.packURL = packURL
    }

    func retrieve(question: String, limit: Int = 3) throws -> KnowledgePackRetrieval {
        guard FileManager.default.fileExists(atPath: packURL.path) else {
            throw KnowledgePackError.noDownloadedPack
        }

        var db: OpaquePointer?
        let flags = SQLITE_OPEN_READONLY | SQLITE_OPEN_FULLMUTEX
        guard sqlite3_open_v2(packURL.path, &db, flags, nil) == SQLITE_OK, let db else {
            let message = db.flatMap { sqlite3_errmsg($0) }.map { String(cString: $0) } ?? "unknown error"
            if let db { sqlite3_close(db) }
            throw KnowledgePackError.openFailed(message)
        }
        defer { sqlite3_close(db) }

        let tokens = Self.tokens(in: question)
        guard !tokens.isEmpty else {
            return KnowledgePackRetrieval(question: question, hits: [])
        }

        let sections = try loadSections(db: db)
        let ranked = sections.compactMap { section -> (Section, Double)? in
            let score = Self.score(section.text, title: section.title, tokens: tokens)
            return score > 0 ? (section, score) : nil
        }
        .sorted { lhs, rhs in
            if lhs.1 == rhs.1 { return lhs.0.title < rhs.0.title }
            return lhs.1 > rhs.1
        }
        .prefix(limit)

        let hits = ranked.enumerated().map { index, item in
            KnowledgePackHit(
                citationIndex: index + 1,
                sectionID: item.0.id,
                title: item.0.title,
                body: Self.excerpt(from: item.0.body, around: Array(tokens)),
                docTitle: item.0.docTitle,
                sourcePage: item.0.sourcePage,
                score: item.1
            )
        }
        return KnowledgePackRetrieval(question: question, hits: hits)
    }

    private func loadSections(db: OpaquePointer) throws -> [Section] {
        let sql = """
        SELECT
          w.id,
          w.doc_title,
          w.title,
          w.body,
          COALESCE((
            SELECT c.source_page
            FROM chunks c
            WHERE c.doc_id = w.doc_id
            ORDER BY c.chunk_index ASC
            LIMIT 1
          ), '') AS source_page
        FROM wiki_sections w
        ORDER BY w.doc_title ASC, w.section_index ASC
        """

        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &statement, nil) == SQLITE_OK, let statement else {
            throw KnowledgePackError.queryFailed(String(cString: sqlite3_errmsg(db)))
        }
        defer { sqlite3_finalize(statement) }

        var sections: [Section] = []
        while sqlite3_step(statement) == SQLITE_ROW {
            let id = Self.text(statement, 0)
            let docTitle = Self.text(statement, 1)
            let title = Self.text(statement, 2)
            let body = Self.text(statement, 3)
            let sourcePage = Self.text(statement, 4)
            sections.append(Section(
                id: id,
                docTitle: docTitle,
                title: title,
                body: body,
                sourcePage: sourcePage,
                text: "\(docTitle) \(title) \(body)"
            ))
        }
        return sections
    }

    static func tokens(in text: String) -> Set<String> {
        let stop: Set<String> = [
            "about", "after", "again", "also", "and", "are", "can", "could", "does",
            "for", "from", "how", "into", "is", "it", "its", "of", "on", "or",
            "should", "that", "the", "their", "there", "this", "to", "what", "when",
            "where", "which", "with", "would", "you", "your"
        ]
        return Set(text.lowercased()
            .split { !$0.isLetter && !$0.isNumber }
            .map(String.init)
            .filter { $0.count >= 3 && !stop.contains($0) })
    }

    static func score(_ text: String, title: String, tokens: Set<String>) -> Double {
        let haystack = text.lowercased()
        let titleHaystack = title.lowercased()
        return tokens.reduce(0) { total, token in
            var next = total
            if haystack.contains(token) { next += 1 }
            if titleHaystack.contains(token) { next += 2 }
            return next
        }
    }

    static func excerpt(from text: String, around tokens: [String], maxLength: Int = 320) -> String {
        let clean = text.replacingOccurrences(of: "\n", with: " ")
            .replacingOccurrences(of: "  ", with: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard clean.count > maxLength else { return clean }

        let lower = clean.lowercased()
        let firstMatch = tokens.compactMap { lower.range(of: $0)?.lowerBound }.min()
        let start = firstMatch.map { lower.distance(from: lower.startIndex, to: $0) } ?? 0
        let offset = max(0, start - 80)
        let begin = clean.index(clean.startIndex, offsetBy: offset)
        let end = clean.index(begin, offsetBy: min(maxLength, clean.distance(from: begin, to: clean.endIndex)))
        let prefix = offset > 0 ? "..." : ""
        let suffix = end < clean.endIndex ? "..." : ""
        return prefix + String(clean[begin..<end]) + suffix
    }

    private static func text(_ statement: OpaquePointer, _ index: Int32) -> String {
        guard let raw = sqlite3_column_text(statement, index) else { return "" }
        return String(cString: raw)
    }
}
