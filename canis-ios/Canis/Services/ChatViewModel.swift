import Foundation

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = [
        ChatMessage(role: .assistant, content: "Choose a downloaded model and ask a question. All inference runs on this iPhone.")
    ]
    @Published var draft = ""
    @Published var isStreaming = false
    @Published var errorMessage: String?

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

        streamTask = Task {
            do {
                for try await token in await CanisMLXEngine.shared.generate(prompt: text, model: model) {
                    guard !Task.isCancelled, assistantIndex < messages.count else { return }
                    messages[assistantIndex].content += token
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
    }

    func clear() {
        stop()
        messages = [
            ChatMessage(role: .assistant, content: "Choose a downloaded model and ask a question. All inference runs on this iPhone.")
        ]
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
