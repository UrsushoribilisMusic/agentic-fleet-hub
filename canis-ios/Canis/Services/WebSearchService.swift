import Foundation

/// Brave Search API client for Canis web-search tool.
///
/// Privacy: queries leave the device to Brave Search (api.search.brave.com).
/// This is explicitly opt-in per CANIS-D spec — off by default, disclosed in UI.
/// Users who need full on-device sovereignty can point SEARXNG_URL to a local instance.
actor WebSearchService {
    static let shared = WebSearchService()

    private let session: URLSession
    private let braveAPIURL = URL(string: "https://api.search.brave.com/res/v1/web/search")!
    private let fetchTimeout: TimeInterval = 4.0
    private let searchTimeout: TimeInterval = 8.0
    private let maxBodyChars = 900

    private init() {
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = 8
        config.timeoutIntervalForResource = 12
        session = URLSession(configuration: config)
    }

    // MARK: - Public

    /// Fetch top-N results from Brave Search and enrich the top-3 with body text.
    func search(query: String, topN: Int = 5) async throws -> [WebSearchResult] {
        var results = try await fetchBraveResults(query: query, count: topN)
        results = await enrich(results: results, topN: min(3, topN))
        return results
    }

    // MARK: - Private

    private func fetchBraveResults(query: String, count: Int) async throws -> [WebSearchResult] {
        guard let apiKey = apiKey(), !apiKey.isEmpty else {
            throw WebSearchError.missingAPIKey
        }
        var comps = URLComponents(url: braveAPIURL, resolvingAgainstBaseURL: false)!
        comps.queryItems = [
            URLQueryItem(name: "q", value: query),
            URLQueryItem(name: "count", value: "\(count)"),
            URLQueryItem(name: "safesearch", value: "moderate"),
            URLQueryItem(name: "text_decorations", value: "0"),
        ]
        guard let url = comps.url else { throw WebSearchError.badURL }
        var req = URLRequest(url: url, timeoutInterval: searchTimeout)
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        req.setValue(apiKey, forHTTPHeaderField: "X-Subscription-Token")

        let (data, resp) = try await session.data(for: req)
        guard let http = resp as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw WebSearchError.httpError((resp as? HTTPURLResponse)?.statusCode ?? 0)
        }
        return try parseBraveResponse(data: data)
    }

    private func parseBraveResponse(data: Data) throws -> [WebSearchResult] {
        struct BraveResponse: Decodable {
            struct WebResults: Decodable { let results: [BraveResult]? }
            struct BraveResult: Decodable { let title: String; let url: String; let description: String? }
            let web: WebResults?
        }
        let decoded = try JSONDecoder().decode(BraveResponse.self, from: data)
        return (decoded.web?.results ?? []).map {
            WebSearchResult(title: $0.title, url: $0.url, snippet: $0.description ?? "", bodyExcerpt: "")
        }
    }

    private func enrich(results: [WebSearchResult], topN: Int) async -> [WebSearchResult] {
        var enriched = results
        await withTaskGroup(of: (Int, String).self) { group in
            for (i, r) in results.prefix(topN).enumerated() {
                group.addTask { [weak self] in
                    guard let self else { return (i, "") }
                    let body = await self.fetchBody(url: r.url)
                    return (i, body)
                }
            }
            for await (i, body) in group {
                if i < enriched.count {
                    enriched[i] = WebSearchResult(
                        title: enriched[i].title,
                        url: enriched[i].url,
                        snippet: enriched[i].snippet,
                        bodyExcerpt: body
                    )
                }
            }
        }
        return enriched
    }

    private func fetchBody(url: String) async -> String {
        guard let parsedURL = URL(string: url) else { return "" }
        var req = URLRequest(url: parsedURL, timeoutInterval: fetchTimeout)
        req.setValue("Canis-Search/1.0", forHTTPHeaderField: "User-Agent")
        guard let (data, _) = try? await session.data(for: req),
              let html = String(data: data, encoding: .utf8) else { return "" }
        return extractText(from: html)
    }

    /// Minimal HTML-to-text: strip tags and collapse whitespace.
    private func extractText(from html: String) -> String {
        var text = html
        // Remove script/style blocks
        let blockPattern = try? NSRegularExpression(pattern: "<(script|style)[^>]*>.*?</\\1>", options: [.caseInsensitive, .dotMatchesLineSeparators])
        if let bp = blockPattern {
            text = bp.stringByReplacingMatches(in: text, range: NSRange(text.startIndex..., in: text), withTemplate: " ")
        }
        // Strip remaining tags
        let tagPattern = try? NSRegularExpression(pattern: "<[^>]+>", options: [])
        if let tp = tagPattern {
            text = tp.stringByReplacingMatches(in: text, range: NSRange(text.startIndex..., in: text), withTemplate: " ")
        }
        // Decode common entities
        text = text.replacingOccurrences(of: "&amp;", with: "&")
            .replacingOccurrences(of: "&lt;", with: "<")
            .replacingOccurrences(of: "&gt;", with: ">")
            .replacingOccurrences(of: "&quot;", with: "\"")
            .replacingOccurrences(of: "&#39;", with: "'")
            .replacingOccurrences(of: "&nbsp;", with: " ")
        // Collapse whitespace
        let words = text.components(separatedBy: .whitespacesAndNewlines).filter { !$0.isEmpty }
        let collapsed = words.joined(separator: " ")
        return String(collapsed.prefix(maxBodyChars))
    }

    private func apiKey() -> String? {
        // Read from bundle Info.plist key "BRAVE_API_KEY" or from an env-injected plist.
        // Secrets are injected at build time via Xcode build settings — never hard-coded.
        Bundle.main.object(forInfoDictionaryKey: "BRAVE_API_KEY") as? String
    }
}

enum WebSearchError: LocalizedError {
    case missingAPIKey
    case badURL
    case httpError(Int)

    var errorDescription: String? {
        switch self {
        case .missingAPIKey: return "Brave API key not configured. Add BRAVE_API_KEY to Info.plist."
        case .badURL: return "Could not construct search URL."
        case .httpError(let code): return "Search API returned HTTP \(code)."
        }
    }
}

// MARK: - Context builder (shared with CanisMLXEngine)

enum SearchContextBuilder {
    static func build(results: [WebSearchResult], query: String) -> String {
        guard !results.isEmpty else { return "" }
        var lines = ["[WEB SEARCH RESULTS — answer from these sources; cite as [1], [2], etc.]"]
        for (i, r) in results.enumerated() {
            let body = r.bodyExcerpt.isEmpty ? r.snippet : r.bodyExcerpt
            lines.append("\n[\(i + 1)] \(r.title)\nURL: \(r.url)\n\(body)")
        }
        lines.append("\n[END RESULTS]\n")
        lines.append("User question: \(query)")
        return lines.joined(separator: "\n")
    }

    static func shouldSearch(in text: String) -> Bool {
        let lower = text.lowercased()
        let uncertaintyPhrases = [
            "i'm not sure", "i don't know", "i cannot confirm", "i'm unable to",
            "i lack", "i don't have", "unclear", "uncertain", "as of my knowledge",
            "my training data", "i can't verify", "i cannot verify",
        ]
        return uncertaintyPhrases.contains { lower.contains($0) }
    }

    static func isLikelyWebQuery(_ text: String) -> Bool {
        let lower = text.lowercased()
        let webHints = [
            "latest", "recent", "current", "today", "now", "this week",
            "2024", "2025", "2026", "price of", "who won", "what happened",
            "breaking", "news", "live", "right now", "as of",
        ]
        return webHints.contains { lower.contains($0) }
    }
}
