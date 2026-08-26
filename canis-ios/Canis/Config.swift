import Foundation

enum Config {
    static let bundleID = "com.bigbearengineering.canis"

    enum CanisAPI {
        static let defaultBaseURL = "http://127.0.0.1:4200/api"
    }

    enum Downloads {
        static func huggingFaceURL(repo: String, file: String) -> URL {
            URL(string: "https://huggingface.co/\(repo)/resolve/main/\(file)")!
        }
    }
}
