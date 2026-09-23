import Foundation
import PDFKit
import Vision

/// A single page of extracted plain text from a user-supplied document.
struct ExtractedPage: Sendable {
    /// 1-based page number.
    let pageNumber: Int
    let text: String
}

enum BoneExtractorError: LocalizedError {
    case encryptedPDF
    case corruptPDF(String)
    case unsupportedFileType(String)
    case readFailed(String)

    var errorDescription: String? {
        switch self {
        case .encryptedPDF:
            return "The PDF is password-protected. Remove the password and try again."
        case .corruptPDF(let name):
            return "Could not open '\(name)' — the file may be corrupt or not a valid PDF."
        case .unsupportedFileType(let ext):
            return "'\(ext)' files are not supported. Import PDF, txt, or md files."
        case .readFailed(let detail):
            return "Could not read the file: \(detail)"
        }
    }
}

/// Extracts clean plain text per page from PDF, txt, and md files.
/// Everything runs on-device; no network access is used.
///
/// Reading-order limitation (v1): PDFKit and Vision extract text in the order
/// it appears in the PDF content stream, which may interleave columns in
/// multi-column layouts or mis-sequence table cells. This is acceptable for
/// keyword-retrieval use cases where semantic overlap matters more than exact
/// reading order.
final class BoneExtractor {

    // Pages whose PDFKit string length falls below this threshold are treated as
    // scanned or image-only pages and routed to Vision OCR.
    private static let minTextThreshold = 10

    /// Extracts text from a PDF, txt, or md file.
    /// - Parameter url: Local file URL. No network access is performed.
    /// - Returns: One `ExtractedPage` per PDF page, or a single page for txt/md.
    func extract(_ url: URL) throws -> [ExtractedPage] {
        switch url.pathExtension.lowercased() {
        case "pdf":
            return try extractPDF(url)
        case "txt", "md", "markdown":
            return try extractPlainText(url)
        default:
            throw BoneExtractorError.unsupportedFileType(url.pathExtension.lowercased())
        }
    }

    // MARK: - PDF

    private func extractPDF(_ url: URL) throws -> [ExtractedPage] {
        guard let doc = PDFDocument(url: url) else {
            throw BoneExtractorError.corruptPDF(url.lastPathComponent)
        }
        if doc.isEncrypted && doc.isLocked {
            throw BoneExtractorError.encryptedPDF
        }

        var pages: [ExtractedPage] = []
        for i in 0..<doc.pageCount {
            guard let page = doc.page(at: i) else { continue }
            let raw = (page.string ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
            let text: String
            if raw.count >= Self.minTextThreshold {
                text = raw
            } else {
                // Scanned or image-only page — fall back to on-device Vision OCR.
                text = (try? ocrPage(page)) ?? raw
            }
            pages.append(ExtractedPage(pageNumber: i + 1, text: text))
        }
        return pages
    }

    /// Renders a PDF page to a high-resolution bitmap and runs Vision OCR on it.
    /// Vision processing via `VNImageRequestHandler.perform` is synchronous;
    /// the completion handler fires before `perform` returns.
    private func ocrPage(_ page: PDFPage) throws -> String {
        // Scale ×2 for better OCR fidelity on typical 72 dpi PDF pages.
        let mediaBox = page.bounds(for: .mediaBox)
        let pixelSize = CGSize(width: mediaBox.width * 2, height: mediaBox.height * 2)

        // PDFPage.thumbnail handles PDF/UIKit coordinate-system differences internally.
        let thumbnail = page.thumbnail(of: pixelSize, for: .mediaBox)
        guard let cgImage = thumbnail.cgImage else { return "" }

        var recognizedText = ""
        let request = VNRecognizeTextRequest { req, _ in
            let observations = req.results as? [VNRecognizedTextObservation] ?? []
            recognizedText = observations
                .compactMap { $0.topCandidates(1).first?.string }
                .joined(separator: "\n")
        }
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = true

        try VNImageRequestHandler(cgImage: cgImage, options: [:]).perform([request])
        return recognizedText.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    // MARK: - Plain text / Markdown

    private func extractPlainText(_ url: URL) throws -> [ExtractedPage] {
        do {
            let text = try String(contentsOf: url, encoding: .utf8)
            return [ExtractedPage(pageNumber: 1, text: text)]
        } catch {
            throw BoneExtractorError.readFailed(error.localizedDescription)
        }
    }
}
