import Foundation

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = [
        ChatMessage(role: .assistant, content: "Choose a downloaded model and ask a question. All inference runs on this iPhone.")
    ]
    @Published var draft = ""
    @Published var isStreaming = false
    @Published var isSearching = false      // CANIS-D: true while web search is in flight
    @Published var searchQuery: String?    // CANIS-D: query shown in UI during search
    @Published var webSearchEnabled = false // CANIS-D: user toggle
    @Published var errorMessage: String?
    @Published var currentReadout: DispositionReadout = .idle

    private var streamTask: Task<Void, Never>?

    func send(using model: CanisModel) {
        let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isStreaming else { return }
        draft = ""
        errorMessage = nil

        messages.append(ChatMessage(role: .user, content: text, modelID: model.rawValue))
        messages.append(ChatMessage(role: .assistant, content: "", modelID: model.rawValue, isStreaming: true))
        let assistantIndex = messages.count - 1
        isStreaming = true
        isSearching = false
        searchQuery = nil
        currentReadout = .idle

        streamTask = Task {
            do {
                let stream = webSearchEnabled
                    ? await CanisMLXEngine.shared.generateWithSearch(prompt: text, model: model)
                    : await CanisMLXEngine.shared.generateWithKnowledge(prompt: text, model: model)
                for try await event in stream {
                    guard !Task.isCancelled, assistantIndex < messages.count else { return }
                    switch event {
                    case .text(let token):
                        messages[assistantIndex].content += token
                    case .disposition(let readout):
                        currentReadout = readout
                        messages[assistantIndex].dispositionReadout = readout
                    case .searchStarted(let query):
                        // Dog enters "searching" activity state
                        isSearching = true
                        searchQuery = query
                    case .searchComplete(let citations):
                        isSearching = false
                        searchQuery = nil
                        messages[assistantIndex].citations = citations
                    }
                }
                finishAssistantMessage(at: assistantIndex)
            } catch {
                guard assistantIndex < messages.count else { return }
                messages[assistantIndex].content = error.localizedDescription
                finishAssistantMessage(at: assistantIndex)
            }
        }
    }

    func stop() {
        streamTask?.cancel()
        streamTask = nil
        if let last = messages.indices.last, messages[last].isStreaming {
            messages[last].isStreaming = false
            if messages[last].content.isEmpty {
                messages[last].content = "Cancelled."
            }
        }
        isStreaming = false
        currentReadout = .idle
    }

    func clear() {
        stop()
        messages = [
            ChatMessage(role: .assistant, content: "Choose a downloaded model and ask a question. All inference runs on this iPhone.")
        ]
        currentReadout = .idle
    }

    private func finishAssistantMessage(at index: Int) {
        guard index < messages.count else { return }
        messages[index].isStreaming = false
        if messages[index].content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            messages[index].content = "No output returned."
        }
        isStreaming = false
        streamTask = nil
    }
}
