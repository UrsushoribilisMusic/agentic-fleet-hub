import Foundation

struct WebSearchResult: Codable, Identifiable, Equatable, Sendable {
    var id: String { url }
    let title: String
    let url: String
    let snippet: String
    let bodyExcerpt: String

    enum CodingKeys: String, CodingKey {
        case title, url, snippet
        case bodyExcerpt = "body_excerpt"
    }
}

extension WebSearchResult {
    var displayURL: String {
        URL(string: url)?.host ?? url
    }

    var citationText: String {
        bodyExcerpt.isEmpty ? snippet : bodyExcerpt
    }
}
