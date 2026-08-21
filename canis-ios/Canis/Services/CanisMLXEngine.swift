import Foundation
import MLX
import MLXLLM
import MLXLMCommon
import UIKit

enum CanisMLXError: LocalizedError {
    case modelNotDownloaded(String)
    case noModelLoaded
    case thermal(ProcessInfo.ThermalState)
    case backgroundExecution

    var errorDescription: String? {
        switch self {
        case .modelNotDownloaded(let name):
            return "\(name) is not downloaded yet."
        case .noModelLoaded:
            return "No model is loaded."
        case .thermal(let state):
            return "The device is too warm to run Canis right now (\(state))."
        case .backgroundExecution:
            return "Canis cannot run MLX while the app is in the background."
        }
    }
}

actor CanisMLXEngine {
    static let shared = CanisMLXEngine()

    private var container: ModelContainer?
    private var loadedModel: CanisModel?
    private var currentTask: Task<Void, Never>?
    private var generating = false

    private init() {
        MLX.Memory.cacheLimit = 20 * 1024 * 1024
        NotificationCenter.default.addObserver(
            forName: UIApplication.willResignActiveNotification,
            object: nil,
            queue: .main
        ) { _ in Task { await CanisMLXEngine.shared.interruptAndUnload() } }
        NotificationCenter.default.addObserver(
            forName: UIApplication.didEnterBackgroundNotification,
            object: nil,
            queue: .main
        ) { _ in Task { await CanisMLXEngine.shared.interruptAndUnload() } }
    }

    func handleMemoryPressure() {
        MLX.Memory.clearCache()
        if !generating { unload() }
    }

    func interruptAndUnload() {
        generating = false
        unload()
    }

    func unload() {
        currentTask?.cancel()
        currentTask = nil
        container = nil
        loadedModel = nil
        MLX.Memory.clearCache()
    }

    func unloadIfLoaded(modelID: String) {
        guard loadedModel?.rawValue == modelID else { return }
        unload()
    }

    func load(model: CanisModel) async throws {
        if loadedModel == model, container != nil { return }

        let active = await MainActor.run { UIApplication.shared.applicationState == .active }
        guard active else { throw CanisMLXError.backgroundExecution }
        guard FileManager.default.fileExists(atPath: model.localDirectory.appendingPathComponent("config.json").path) else {
            throw CanisMLXError.modelNotDownloaded(model.displayName)
        }

        let thermal = ProcessInfo.processInfo.thermalState
        if thermal == .critical { throw CanisMLXError.thermal(thermal) }
        if thermal == .serious {
            try? await Task.sleep(nanoseconds: 5_000_000_000)
            let after = ProcessInfo.processInfo.thermalState
            if after == .serious || after == .critical {
                throw CanisMLXError.thermal(after)
            }
        }

        container = nil
        loadedModel = nil
        MLX.Memory.clearCache()
        try? await Task.sleep(nanoseconds: 700_000_000)

        container = try await loadModelContainer(directory: model.localDirectory)
        loadedModel = model
    }

    func generate(prompt: String, model: CanisModel, maxTokens: Int = 700) -> AsyncThrowingStream<CanisGenerationEvent, Error> {
        AsyncThrowingStream { continuation in
            let task = Task {
                do {
                    try await load(model: model)
                    guard let container else { throw CanisMLXError.noModelLoaded }

                    let active = await MainActor.run { UIApplication.shared.applicationState == .active }
                    guard active else { throw CanisMLXError.backgroundExecution }

                    let thermal = ProcessInfo.processInfo.thermalState
                    if thermal == .serious || thermal == .critical {
                        throw CanisMLXError.thermal(thermal)
                    }

                    generating = true
                    MLX.Memory.clearCache()
                    let session = MLXLMCommon.ChatSession(
                        container,
                        instructions: Self.systemPrompt,
                        generateParameters: GenerateParameters(temperature: 0.6, topP: 0.9)
                    )
                    let dispositionEngine = DispositionReadoutEngine(model: model)
                    var generatedText = ""
                    var tokenCount = 0
                    for try await chunk in session.streamResponse(to: prompt) {
                        if Task.isCancelled { break }
                        generatedText += chunk
                        continuation.yield(.text(chunk))
                        let readout = dispositionEngine.fallbackReadout(
                            generatedText: generatedText,
                            latestChunk: chunk
                        )
                        continuation.yield(.disposition(readout))
                        tokenCount += 1
                        if tokenCount >= maxTokens { break }
                        if tokenCount % 10 == 0 {
                            let stillActive = await MainActor.run { UIApplication.shared.applicationState == .active }
                            if !stillActive { break }
                            await Task.yield()
                        }
                    }
                    generating = false
                    continuation.finish()
                } catch {
                    generating = false
                    continuation.finish(throwing: error)
                }
            }
            currentTask = task
            continuation.onTermination = { _ in task.cancel() }
        }
    }

    private static let systemPrompt = """
    You are Canis, a concise on-device assistant. Answer directly, be honest about uncertainty, and never claim cloud access. Keep replies useful and compact unless the user asks for depth.
    """
}
