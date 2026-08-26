import Foundation

enum KnowledgePackState: Equatable {
    case notInstalled
    case checking
    case downloading(Double)
    case ready(version: Int, docCount: Int, wikiSectionCount: Int)
    case failed(String)

    var isReady: Bool {
        if case .ready = self { return true }
        return false
    }
}

@MainActor
final class KnowledgePackStore: ObservableObject {
    static let shared = KnowledgePackStore()

    nonisolated static var directoryURL: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("knowledge-packs", isDirectory: true)
    }

    nonisolated static var currentPackURL: URL {
        directoryURL.appendingPathComponent("current.sqlite")
    }

    private struct PackStatus: Decodable {
        let version: Int
        let chunkCount: Int
        let docCount: Int
        let wikiSectionCount: Int
        let status: String
    }

    private struct InstalledMetadata: Codable {
        let version: Int
        let docCount: Int
        let wikiSectionCount: Int
        let installedAt: Date
    }

    @Published private(set) var state: KnowledgePackState = .checking
    @Published var apiToken: String = ""
    @Published var apiBaseURLString: String = Config.CanisAPI.defaultBaseURL

    private static let tokenKey = "canis.apiToken"
    private static let apiBaseURLKey = "canis.apiBaseURL"
    private static let metadataFile = "installed-pack.json"

    private init() {}

    func setup() {
        apiToken = UserDefaults.standard.string(forKey: Self.tokenKey) ?? ""
        apiBaseURLString = UserDefaults.standard.string(forKey: Self.apiBaseURLKey) ?? Config.CanisAPI.defaultBaseURL
        state = readInstalledState()
    }

    func saveSettings(token: String, apiBaseURLString: String) {
        apiToken = token.trimmingCharacters(in: .whitespacesAndNewlines)
        self.apiBaseURLString = apiBaseURLString.trimmingCharacters(in: .whitespacesAndNewlines)
        UserDefaults.standard.set(apiToken, forKey: Self.tokenKey)
        UserDefaults.standard.set(self.apiBaseURLString, forKey: Self.apiBaseURLKey)
    }

    func saveToken(_ token: String) {
        saveSettings(token: token, apiBaseURLString: apiBaseURLString)
    }

    func downloadLatest() async {
        let token = apiToken.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !token.isEmpty else {
            state = .failed("Paste the Canis session token before downloading the pack.")
            return
        }

        state = .checking
        do {
            let status = try await fetchStatus(token: token)
            guard status.version > 0, status.status == "ready" else {
                state = .failed("No ready pack is available yet.")
                return
            }

            state = .downloading(0)
            var request = URLRequest(url: try apiBaseURL().appendingPathComponent("pack/download"))
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            let (downloadURL, response) = try await URLSession.shared.download(for: request)
            guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
                state = .failed("Pack download failed.")
                return
            }

            try FileManager.default.createDirectory(at: Self.directoryURL, withIntermediateDirectories: true)
            let destination = Self.currentPackURL
            if FileManager.default.fileExists(atPath: destination.path) {
                try FileManager.default.removeItem(at: destination)
            }
            try FileManager.default.moveItem(at: downloadURL, to: destination)
            try writeMetadata(version: status.version, docCount: status.docCount, wikiSectionCount: status.wikiSectionCount)
            state = .ready(version: status.version, docCount: status.docCount, wikiSectionCount: status.wikiSectionCount)
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    func deletePack() {
        try? FileManager.default.removeItem(at: Self.currentPackURL)
        try? FileManager.default.removeItem(at: metadataURL)
        state = .notInstalled
    }

    private func fetchStatus(token: String) async throws -> PackStatus {
        var request = URLRequest(url: try apiBaseURL().appendingPathComponent("pack/status"))
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.userAuthenticationRequired)
        }
        return try JSONDecoder().decode(PackStatus.self, from: data)
    }

    private func apiBaseURL() throws -> URL {
        guard let url = URL(string: apiBaseURLString.trimmingCharacters(in: .whitespacesAndNewlines)) else {
            throw URLError(.badURL)
        }
        return url
    }

    private func readInstalledState() -> KnowledgePackState {
        guard FileManager.default.fileExists(atPath: Self.currentPackURL.path) else {
            return .notInstalled
        }
        guard let data = try? Data(contentsOf: metadataURL),
              let metadata = try? JSONDecoder().decode(InstalledMetadata.self, from: data)
        else {
            return .ready(version: 0, docCount: 0, wikiSectionCount: 0)
        }
        return .ready(
            version: metadata.version,
            docCount: metadata.docCount,
            wikiSectionCount: metadata.wikiSectionCount
        )
    }

    private func writeMetadata(version: Int, docCount: Int, wikiSectionCount: Int) throws {
        let metadata = InstalledMetadata(
            version: version,
            docCount: docCount,
            wikiSectionCount: wikiSectionCount,
            installedAt: Date()
        )
        let data = try JSONEncoder().encode(metadata)
        try data.write(to: metadataURL, options: .atomic)
    }

    private var metadataURL: URL {
        Self.directoryURL.appendingPathComponent(Self.metadataFile)
    }
}
