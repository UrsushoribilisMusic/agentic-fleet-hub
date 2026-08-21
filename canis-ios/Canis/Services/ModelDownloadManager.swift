import Combine
import CryptoKit
import Foundation
import Network

struct ModelTransferProgress: Sendable, Equatable {
    let modelID: String
    let completedFiles: Int
    let totalFiles: Int
    let bytesReceived: Int64
    let bytesExpected: Int64
    var errorMessage: String?

    var fraction: Double {
        guard totalFiles > 0 else { return 0 }
        let currentFile = bytesExpected > 0 ? min(1, Double(bytesReceived) / Double(bytesExpected)) : 0
        return (Double(completedFiles) + currentFile) / Double(totalFiles)
    }

    var displayText: String {
        guard totalFiles > 0 else { return "Preparing..." }
        if bytesExpected > 0 {
            let received = ByteCountFormatter.string(fromByteCount: bytesReceived, countStyle: .file)
            let expected = ByteCountFormatter.string(fromByteCount: bytesExpected, countStyle: .file)
            return "File \(completedFiles + 1) of \(totalFiles) - \(received) / \(expected)"
        }
        return "\(completedFiles) of \(totalFiles) files"
    }

    static func preparing(modelID: String, fileCount: Int) -> Self {
        Self(modelID: modelID, completedFiles: 0, totalFiles: fileCount, bytesReceived: 0, bytesExpected: 0)
    }
}

enum ModelDownloadState: Equatable {
    case notDownloaded
    case downloading(ModelTransferProgress)
    case paused(String)
    case downloaded
    case failed(String)

    var isDownloaded: Bool {
        if case .downloaded = self { return true }
        return false
    }

    var isActive: Bool {
        if case .downloading = self { return true }
        return false
    }
}

private struct PendingManifest: Codable {
    struct Entry: Codable {
        let name: String
        let urlString: String
    }

    let files: [Entry]
    let localDirectoryPath: String
}

private struct PersistedDownloadState: Codable {
    var completedModels: Set<String> = []
    var verifiedFiles: [String: Set<String>] = [:]
    var pendingManifests: [String: PendingManifest] = [:]
}

final class ModelDownloadSessionDelegate: NSObject, URLSessionDownloadDelegate {
    weak var manager: ModelDownloadManager?

    func urlSession(
        _ session: URLSession,
        downloadTask: URLSessionDownloadTask,
        didWriteData bytesWritten: Int64,
        totalBytesWritten: Int64,
        totalBytesExpectedToWrite: Int64
    ) {
        Task {
            await manager?.taskDidProgress(
                id: downloadTask.taskIdentifier,
                received: totalBytesWritten,
                expected: totalBytesExpectedToWrite
            )
        }
    }

    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask, didFinishDownloadingTo location: URL) {
        let tmp = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        do {
            try FileManager.default.copyItem(at: location, to: tmp)
            Task { await manager?.taskDidFinishDownloading(id: downloadTask.taskIdentifier, tmpURL: tmp) }
        } catch {
            Task { await manager?.taskDidFail(id: downloadTask.taskIdentifier, error: error) }
        }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        guard let error else { return }
        Task { await manager?.taskDidFail(id: task.taskIdentifier, error: error) }
    }

    func urlSessionDidFinishEvents(forBackgroundURLSession session: URLSession) {
        Task { await manager?.sessionDidFinishBackgroundEvents() }
    }
}

actor ModelDownloadManager: ObservableObject {
    static let shared = ModelDownloadManager()

    private static let stateFile = "canis_download_state.json"
    private static let sessionID = "\(Config.bundleID).models.bg"

    @MainActor @Published var states: [String: ModelDownloadState] = [:]
    @MainActor @Published var networkAvailable = true
    @MainActor @Published var wifiDownloadAllowed = true
    @MainActor @Published var storageUsageBytes: [String: Int64] = [:]

    private struct Job {
        let modelID: String
        let files: [DownloadFile]
        let localDirectory: URL
        var pendingFiles: [DownloadFile]
        var currentTask: URLSessionDownloadTask?
        var currentTaskID: Int?
        var completedCount: Int { files.count - pendingFiles.count }
    }

    let sessionDelegate = ModelDownloadSessionDelegate()
    private var backgroundCompletion: (() -> Void)?
    private var sessionStorage: URLSession?
    private var persisted = PersistedDownloadState()
    private var jobs: [String: Job] = [:]
    private var taskToModel: [Int: String] = [:]
    private var monitor: NWPathMonitor?
    private let monitorQueue = DispatchQueue(label: "canis.download.netmon", qos: .utility)
    private var downloadsAllowed = true
    private var pauseReason = "Waiting for network..."
    private var lastPath: NWPath?

    #if DEBUG
    private static let cellularBypassKey = "canis.allowCellularDownload"
    private var cellularBypassActive = false
    #endif

    private init() {}

    func setup() {
        sessionDelegate.manager = self
        loadPersistedState()
        #if DEBUG
        cellularBypassActive = UserDefaults.standard.bool(forKey: Self.cellularBypassKey)
        #endif
        startNetworkMonitor()
        reconnectBackgroundSession()
        rebuildPublishedState()
    }

    func startDownload(_ model: CanisModel) {
        let modelID = model.rawValue
        jobs[modelID]?.currentTask?.cancel()
        jobs[modelID] = nil
        purgeUnlistedFiles(in: model.localDirectory, manifest: model.files)

        let remaining = remainingFiles(modelID: modelID, allFiles: model.files)
        guard !remaining.isEmpty else {
            markComplete(modelID: modelID, files: model.files, localDirectory: model.localDirectory)
            return
        }

        persisted.pendingManifests[modelID] = PendingManifest(
            files: model.files.map { .init(name: $0.name, urlString: $0.url.absoluteString) },
            localDirectoryPath: model.localDirectory.path
        )
        savePersistedState()
        jobs[modelID] = Job(modelID: modelID, files: model.files, localDirectory: model.localDirectory, pendingFiles: remaining)

        Task { @MainActor in
            self.states[modelID] = .downloading(.preparing(modelID: modelID, fileCount: model.files.count))
        }
        startNextFile(modelID: modelID)
    }

    func resumeDownload(_ model: CanisModel) {
        if jobs[model.rawValue] == nil {
            startDownload(model)
        } else {
            startNextFile(modelID: model.rawValue)
        }
    }

    func cancelDownload(_ model: CanisModel) {
        let modelID = model.rawValue
        jobs[modelID]?.currentTask?.cancel()
        if let id = jobs[modelID]?.currentTaskID {
            taskToModel.removeValue(forKey: id)
        }
        jobs.removeValue(forKey: modelID)
        persisted.pendingManifests.removeValue(forKey: modelID)
        savePersistedState()
        Task { @MainActor in self.states[modelID] = .notDownloaded }
    }

    func deleteModel(_ model: CanisModel) {
        cancelDownload(model)
        try? FileManager.default.removeItem(at: model.localDirectory)
        persisted.completedModels.remove(model.rawValue)
        persisted.verifiedFiles.removeValue(forKey: model.rawValue)
        persisted.pendingManifests.removeValue(forKey: model.rawValue)
        savePersistedState()
        Task { @MainActor in
            self.states[model.rawValue] = .notDownloaded
            self.storageUsageBytes[model.rawValue] = 0
        }
        Task { await CanisMLXEngine.shared.unloadIfLoaded(modelID: model.rawValue) }
    }

    func isDownloaded(_ model: CanisModel) -> Bool {
        FileManager.default.fileExists(atPath: model.localDirectory.appendingPathComponent(".complete").path)
    }

    nonisolated func hasSufficientSpace(for bytes: Int64) -> Bool {
        guard let attrs = try? FileManager.default.attributesOfFileSystem(forPath: FileManager.default.temporaryDirectory.path),
              let free = attrs[.systemFreeSize] as? Int64
        else { return true }
        return free > Int64(Double(bytes) * 1.1)
    }

    func refreshStorageUsage() {
        var usage: [String: Int64] = [:]
        for model in CanisModel.allCases {
            usage[model.rawValue] = directorySize(model.localDirectory)
        }
        Task { @MainActor in self.storageUsageBytes = usage }
    }

    func handleBackgroundEvent(identifier: String, completionHandler: @escaping () -> Void) {
        guard identifier == Self.sessionID else {
            completionHandler()
            return
        }
        backgroundCompletion = completionHandler
        _ = session
    }

    #if DEBUG
    func setCellularBypass(_ enabled: Bool) {
        cellularBypassActive = enabled
        UserDefaults.standard.set(enabled, forKey: Self.cellularBypassKey)
        sessionStorage?.invalidateAndCancel()
        sessionStorage = nil
        if let lastPath { handlePathChange(path: lastPath) }
    }
    #endif

    func taskDidProgress(id: Int, received: Int64, expected: Int64) {
        guard let modelID = taskToModel[id], let job = jobs[modelID] else { return }
        let progress = ModelTransferProgress(
            modelID: modelID,
            completedFiles: job.completedCount,
            totalFiles: job.files.count,
            bytesReceived: received,
            bytesExpected: expected
        )
        Task { @MainActor in self.states[modelID] = .downloading(progress) }
    }

    func taskDidFinishDownloading(id: Int, tmpURL: URL) {
        guard let modelID = taskToModel[id], var job = jobs[modelID] else {
            try? FileManager.default.removeItem(at: tmpURL)
            return
        }
        taskToModel.removeValue(forKey: id)
        job.currentTask = nil
        job.currentTaskID = nil

        let file = job.pendingFiles[0]
        let destination = job.localDirectory.appendingPathComponent(file.name)
        do {
            try FileManager.default.createDirectory(at: job.localDirectory, withIntermediateDirectories: true)
            if FileManager.default.fileExists(atPath: destination.path) {
                try FileManager.default.removeItem(at: destination)
            }
            try FileManager.default.moveItem(at: tmpURL, to: destination)
        } catch {
            jobs[modelID] = job
            fail(modelID: modelID, reason: "File move failed: \(error.localizedDescription)")
            return
        }

        if let expectedHash = file.sha256, !verifySHA256(at: destination, expected: expectedHash) {
            try? FileManager.default.removeItem(at: destination)
            jobs[modelID] = job
            startNextFile(modelID: modelID)
            return
        }

        var verified = persisted.verifiedFiles[modelID] ?? []
        verified.insert(file.name)
        persisted.verifiedFiles[modelID] = verified
        savePersistedState()

        job.pendingFiles.removeFirst()
        jobs[modelID] = job
        if job.pendingFiles.isEmpty {
            markComplete(modelID: modelID, files: job.files, localDirectory: job.localDirectory)
        } else {
            startNextFile(modelID: modelID)
        }
    }

    func taskDidFail(id: Int, error: Error) {
        guard let modelID = taskToModel[id], var job = jobs[modelID] else { return }
        taskToModel.removeValue(forKey: id)

        if let resumeData = (error as NSError).userInfo[NSURLSessionDownloadTaskResumeData] as? Data {
            let file = job.pendingFiles[0]
            let url = job.localDirectory.appendingPathComponent(file.name + ".resume")
            try? FileManager.default.createDirectory(at: job.localDirectory, withIntermediateDirectories: true)
            try? resumeData.write(to: url, options: .atomic)
        }

        job.currentTask = nil
        job.currentTaskID = nil
        jobs[modelID] = job
        if (error as NSError).code != NSURLErrorCancelled {
            fail(modelID: modelID, reason: error.localizedDescription)
        }
    }

    func sessionDidFinishBackgroundEvents() {
        let handler = backgroundCompletion
        backgroundCompletion = nil
        DispatchQueue.main.async { handler?() }
    }

    private var session: URLSession {
        if let sessionStorage { return sessionStorage }
        let config = URLSessionConfiguration.background(withIdentifier: Self.sessionID)
        config.sessionSendsLaunchEvents = true
        config.isDiscretionary = false
        #if DEBUG
        let cellular = cellularBypassActive
        #else
        let cellular = false
        #endif
        config.allowsCellularAccess = cellular
        config.allowsExpensiveNetworkAccess = cellular
        let newSession = URLSession(configuration: config, delegate: sessionDelegate, delegateQueue: nil)
        sessionStorage = newSession
        return newSession
    }

    private func startNextFile(modelID: String) {
        guard downloadsAllowed else {
            let reason = pauseReason
            Task { @MainActor in self.states[modelID] = .paused(reason) }
            return
        }
        guard var job = jobs[modelID], !job.pendingFiles.isEmpty else { return }

        let file = job.pendingFiles[0]
        let resumeURL = job.localDirectory.appendingPathComponent(file.name + ".resume")
        let task: URLSessionDownloadTask
        if let resumeData = try? Data(contentsOf: resumeURL) {
            task = session.downloadTask(withResumeData: resumeData)
        } else {
            task = session.downloadTask(with: URLRequest(url: file.url))
        }

        try? FileManager.default.removeItem(at: job.localDirectory.appendingPathComponent(file.name))
        try? FileManager.default.removeItem(at: resumeURL)
        task.taskDescription = modelID
        job.currentTask = task
        job.currentTaskID = task.taskIdentifier
        jobs[modelID] = job
        taskToModel[task.taskIdentifier] = modelID
        task.resume()
    }

    private func markComplete(modelID: String, files: [DownloadFile], localDirectory: URL) {
        try? FileManager.default.createDirectory(at: localDirectory, withIntermediateDirectories: true)
        try? "complete".write(to: localDirectory.appendingPathComponent(".complete"), atomically: true, encoding: .utf8)
        persisted.completedModels.insert(modelID)
        persisted.pendingManifests.removeValue(forKey: modelID)
        savePersistedState()
        jobs.removeValue(forKey: modelID)
        refreshStorageUsage()
        Task { @MainActor in self.states[modelID] = .downloaded }
    }

    private func fail(modelID: String, reason: String) {
        jobs.removeValue(forKey: modelID)
        persisted.pendingManifests.removeValue(forKey: modelID)
        savePersistedState()
        Task { @MainActor in self.states[modelID] = .failed(reason) }
    }

    private func purgeUnlistedFiles(in directory: URL, manifest files: [DownloadFile]) {
        guard let names = try? FileManager.default.contentsOfDirectory(atPath: directory.path) else { return }
        let keep = Set(files.map(\.name))
        for name in names {
            if name == ".complete" { continue }
            if keep.contains(name) { continue }
            if name.hasSuffix(".resume"), keep.contains(String(name.dropLast(7))) { continue }
            try? FileManager.default.removeItem(at: directory.appendingPathComponent(name))
        }
    }

    private func remainingFiles(modelID: String, allFiles: [DownloadFile]) -> [DownloadFile] {
        let done = persisted.verifiedFiles[modelID] ?? []
        return allFiles.filter { !done.contains($0.name) }
    }

    private var stateURL: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent(Self.stateFile)
    }

    private func loadPersistedState() {
        guard let data = try? Data(contentsOf: stateURL),
              let decoded = try? JSONDecoder().decode(PersistedDownloadState.self, from: data)
        else { return }
        persisted = decoded
    }

    private func savePersistedState() {
        guard let data = try? JSONEncoder().encode(persisted) else { return }
        try? data.write(to: stateURL, options: .atomic)
    }

    private func rebuildPublishedState() {
        refreshStorageUsage()
        var next: [String: ModelDownloadState] = [:]
        for model in CanisModel.allCases {
            if isDownloaded(model) {
                next[model.rawValue] = .downloaded
            } else if persisted.pendingManifests[model.rawValue] != nil {
                next[model.rawValue] = .paused("Ready to resume")
            } else {
                next[model.rawValue] = .notDownloaded
            }
        }
        Task { @MainActor in self.states = next }
    }

    private func reconnectBackgroundSession() {
        session.getAllTasks { [weak self] tasks in
            Task { [weak self] in await self?.reconcileRestoredTasks(tasks) }
        }
    }

    private func reconcileRestoredTasks(_ tasks: [URLSessionTask]) {
        for task in tasks {
            guard let modelID = task.taskDescription,
                  let downloadTask = task as? URLSessionDownloadTask,
                  let manifest = persisted.pendingManifests[modelID]
            else { continue }

            let directory = URL(fileURLWithPath: manifest.localDirectoryPath)
            let files = manifest.files.compactMap { entry -> DownloadFile? in
                guard let url = URL(string: entry.urlString) else { return nil }
                return DownloadFile(name: entry.name, url: url)
            }
            var job = Job(modelID: modelID, files: files, localDirectory: directory, pendingFiles: remainingFiles(modelID: modelID, allFiles: files))
            job.currentTask = downloadTask
            job.currentTaskID = task.taskIdentifier
            jobs[modelID] = job
            taskToModel[task.taskIdentifier] = modelID
            Task { @MainActor in
                self.states[modelID] = .downloading(.preparing(modelID: modelID, fileCount: files.count))
            }
        }
    }

    private func startNetworkMonitor() {
        let monitor = NWPathMonitor()
        monitor.pathUpdateHandler = { [weak self] path in
            Task { await self?.handlePathChange(path: path) }
        }
        monitor.start(queue: monitorQueue)
        self.monitor = monitor
    }

    private func handlePathChange(path: NWPath) {
        lastPath = path
        let satisfied = path.status == .satisfied
        #if DEBUG
        let allowed = satisfied && (cellularBypassActive || path.usesInterfaceType(.wifi))
        #else
        let allowed = satisfied && path.usesInterfaceType(.wifi)
        #endif
        let wasAllowed = downloadsAllowed
        downloadsAllowed = allowed
        pauseReason = (satisfied && !allowed) ? "Wi-Fi required for model downloads" : "Waiting for network..."
        Task { @MainActor in
            self.networkAvailable = satisfied
            self.wifiDownloadAllowed = allowed
        }

        if allowed && !wasAllowed {
            for modelID in jobs.keys where jobs[modelID]?.currentTaskID == nil {
                startNextFile(modelID: modelID)
            }
        } else if !allowed && wasAllowed {
            pauseActiveTasks(reason: pauseReason)
        }
    }

    private func pauseActiveTasks(reason: String) {
        for (modelID, job) in jobs {
            guard let task = job.currentTask else { continue }
            let localDirectory = job.localDirectory
            let pendingName = job.pendingFiles.first?.name
            taskToModel.removeValue(forKey: task.taskIdentifier)
            var updated = job
            updated.currentTask = nil
            updated.currentTaskID = nil
            jobs[modelID] = updated
            task.cancel(byProducingResumeData: { resumeData in
                guard let resumeData, let pendingName else { return }
                let url = localDirectory.appendingPathComponent(pendingName + ".resume")
                try? FileManager.default.createDirectory(at: localDirectory, withIntermediateDirectories: true)
                try? resumeData.write(to: url, options: .atomic)
            })
            Task { @MainActor in self.states[modelID] = .paused(reason) }
        }
    }

    private func verifySHA256(at url: URL, expected: String) -> Bool {
        guard let handle = try? FileHandle(forReadingFrom: url) else { return false }
        defer { try? handle.close() }
        var hasher = SHA256()
        while true {
            let chunk = (try? handle.read(upToCount: 1_048_576)) ?? Data()
            if chunk.isEmpty { break }
            hasher.update(data: chunk)
        }
        return hasher.finalize().map { String(format: "%02x", $0) }.joined() == expected
    }

    private func directorySize(_ url: URL) -> Int64 {
        guard let enumerator = FileManager.default.enumerator(
            at: url,
            includingPropertiesForKeys: [.isRegularFileKey, .fileSizeKey],
            options: [.skipsHiddenFiles]
        ) else { return 0 }
        var total: Int64 = 0
        for case let fileURL as URL in enumerator {
            guard let values = try? fileURL.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey]),
                  values.isRegularFile == true
            else { continue }
            total += Int64(values.fileSize ?? 0)
        }
        return total
    }
}
