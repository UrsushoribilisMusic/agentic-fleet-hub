import Foundation

struct ChatMessage: Identifiable, Codable, Equatable {
    enum Role: String, Codable {
        case user
        case assistant
    }

    var id = UUID()
    var role: Role
    var content: String
    var modelID: String?
    var dispositionReadout: DispositionReadout?
    var isStreaming = false
    var createdAt = Date()
    // Populated by local pack retrieval or web search for this message.
    var citations: [WebSearchResult] = []
}
