import Foundation

enum Config {
    static let bundleID = "com.bigbearengineering.canis"

    enum Downloads {
        static func huggingFaceURL(repo: String, file: String) -> URL {
            URL(string: "https://huggingface.co/\(repo)/resolve/main/\(file)")!
        }
    }
}
