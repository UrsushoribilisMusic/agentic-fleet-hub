import Foundation

enum CanisModel: String, CaseIterable, Identifiable, Codable {
    case apertus = "canis-apertus"
    case mistralis = "canis-mistralis"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .apertus: return "Canis Apertus"
        case .mistralis: return "Canis Mistralis"
        }
    }

    var subtitle: String {
        switch self {
        case .apertus:
            return "Apertus 1.1 4B Instruct, MLX INT4"
        case .mistralis:
            return "Ministral 3B Instruct, MLX 4-bit"
        }
    }

    var estimatedBytes: Int64 {
        switch self {
        case .apertus: return 2_400_000_000
        case .mistralis: return 2_500_000_000
        }
    }

    var hfRepo: String {
        switch self {
        case .apertus:
            return "swiss-ai/Apertus-v1.1-4B-Instruct-MLX-INT4"
        case .mistralis:
            return "mlx-community/Ministral-3-3B-Instruct-2512-4bit"
        }
    }

    var files: [DownloadFile] {
        let names: [String]
        switch self {
        case .apertus:
            names = [
                "chat_template.jinja",
                "config.json",
                "generation_config.json",
                "merges.txt",
                "model.safetensors",
                "model.safetensors.index.json",
                "special_tokens_map.json",
                "tokenizer.json",
                "tokenizer_config.json",
                "vocab.json",
            ]
        case .mistralis:
            names = [
                "chat_template.jinja",
                "config.json",
                "model.safetensors",
                "model.safetensors.index.json",
                "special_tokens_map.json",
                "tokenizer.json",
                "tokenizer.model",
                "tokenizer_config.json",
            ]
        }
        return names.map { DownloadFile(name: $0, url: Config.Downloads.huggingFaceURL(repo: hfRepo, file: $0)) }
    }

    var localDirectory: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("models/\(rawValue)", isDirectory: true)
    }
}

struct DownloadFile: Codable, Hashable {
    let name: String
    let url: URL
    var sha256: String? = nil
}
