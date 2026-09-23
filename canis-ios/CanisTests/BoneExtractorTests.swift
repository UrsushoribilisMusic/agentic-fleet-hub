import CoreGraphics
import PDFKit
import UIKit
import XCTest
@testable import Canis

final class BoneExtractorTests: XCTestCase {
    private let extractor = BoneExtractor()

    // MARK: - (a) Text PDF

    func testTextPDFExtractsTextFromAllPages() throws {
        let url = try makeTextPDF(pages: [
            "The quick brown fox jumps over the lazy dog.",
            "Page two contains more content about robots and painting."
        ])
        defer { try? FileManager.default.removeItem(at: url) }

        let pages = try extractor.extract(url)

        XCTAssertEqual(pages.count, 2)
        XCTAssertEqual(pages[0].pageNumber, 1)
        XCTAssertTrue(pages[0].text.contains("quick brown fox"),
                      "Page 1 text was: '\(pages[0].text)'")
        XCTAssertEqual(pages[1].pageNumber, 2)
        XCTAssertTrue(pages[1].text.contains("robots"),
                      "Page 2 text was: '\(pages[1].text)'")
    }

    func testTextPDFExtractionIsDeterministic() throws {
        let url = try makeTextPDF(pages: ["Deterministic extraction test content."])
        defer { try? FileManager.default.removeItem(at: url) }

        let first = try extractor.extract(url)
        let second = try extractor.extract(url)

        XCTAssertEqual(first.map(\.text), second.map(\.text))
    }

    // MARK: - (b) Scanned / image-only PDF via Vision OCR

    func testScannedPDFOCRProducesNonEmptyOutput() throws {
        // "CANIS" — all caps, high contrast: maximises OCR reliability on simulator.
        let url = try makeImagePDF(text: "CANIS")
        defer { try? FileManager.default.removeItem(at: url) }

        let pages = try extractor.extract(url)

        XCTAssertEqual(pages.count, 1)
        XCTAssertEqual(pages[0].pageNumber, 1)
        XCTAssertFalse(pages[0].text.isEmpty,
                       "OCR should produce non-empty output for a clear text image")
        // Vision may confuse similar glyphs (0/O, 1/I/l) but should recognise
        // most of a clean high-contrast word. Accept any partial match.
        let lower = pages[0].text.lowercased()
        let matched = lower.contains("canis") || lower.contains("can") ||
                      lower.contains("ani") || lower.contains("nis")
        XCTAssertTrue(matched,
                      "OCR result '\(pages[0].text)' should contain part of 'CANIS'")
    }

    func testScannedPDFOCRIsDeterministic() throws {
        let url = try makeImagePDF(text: "CANIS")
        defer { try? FileManager.default.removeItem(at: url) }

        let first = try extractor.extract(url)
        let second = try extractor.extract(url)

        XCTAssertEqual(first.map(\.text), second.map(\.text))
    }

    // MARK: - (c) Markdown / plain-text file

    func testMarkdownFileExtractsSinglePageWithFullContent() throws {
        let content = "# Bone Notes\n\nSome **markdown** content here.\n\nA second paragraph."
        let url = try writeTempFile(content: content, ext: "md")
        defer { try? FileManager.default.removeItem(at: url) }

        let pages = try extractor.extract(url)

        XCTAssertEqual(pages.count, 1)
        XCTAssertEqual(pages[0].pageNumber, 1)
        XCTAssertEqual(pages[0].text, content)
    }

    func testTxtFileExtractsSinglePage() throws {
        let content = "Plain text content.\nWith two lines."
        let url = try writeTempFile(content: content, ext: "txt")
        defer { try? FileManager.default.removeItem(at: url) }

        let pages = try extractor.extract(url)

        XCTAssertEqual(pages.count, 1)
        XCTAssertEqual(pages[0].text, content)
    }

    // MARK: - Error paths

    func testCorruptPDFThrowsCorruptError() throws {
        let url = try writeTempFile(content: "this is not a pdf file", ext: "pdf")
        defer { try? FileManager.default.removeItem(at: url) }

        XCTAssertThrowsError(try extractor.extract(url)) { error in
            guard case BoneExtractorError.corruptPDF = error else {
                XCTFail("Expected corruptPDF, got \(error)")
                return
            }
        }
    }

    func testEncryptedPDFThrowsEncryptedError() throws {
        let url = try makeEncryptedPDF()
        defer { try? FileManager.default.removeItem(at: url) }

        XCTAssertThrowsError(try extractor.extract(url)) { error in
            guard case BoneExtractorError.encryptedPDF = error else {
                XCTFail("Expected encryptedPDF, got \(error)")
                return
            }
        }
    }

    func testUnsupportedExtensionThrowsError() throws {
        let url = try writeTempFile(content: "<html></html>", ext: "html")
        defer { try? FileManager.default.removeItem(at: url) }

        XCTAssertThrowsError(try extractor.extract(url)) { error in
            guard case BoneExtractorError.unsupportedFileType = error else {
                XCTFail("Expected unsupportedFileType, got \(error)")
                return
            }
        }
    }

    // MARK: - Helpers

    /// Creates a multi-page PDF with selectable vector text on each page.
    /// `UIGraphicsPDFRenderer` embeds real PDF text operators so PDFKit can
    /// extract the string without falling back to OCR.
    private func makeTextPDF(pages: [String]) throws -> URL {
        let pageRect = CGRect(x: 0, y: 0, width: 612, height: 792)
        let renderer = UIGraphicsPDFRenderer(bounds: pageRect)
        let data = renderer.pdfData { ctx in
            for text in pages {
                ctx.beginPage()
                let attrs: [NSAttributedString.Key: Any] = [
                    .font: UIFont.systemFont(ofSize: 14),
                    .foregroundColor: UIColor.black
                ]
                text.draw(
                    in: CGRect(x: 72, y: 72, width: 468, height: 648),
                    withAttributes: attrs
                )
            }
        }
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("bone-text-\(UUID().uuidString).pdf")
        try data.write(to: url)
        return url
    }

    /// Creates a single-page PDF whose content is a rasterized bitmap image —
    /// no text operators in the PDF stream. BoneExtractor sees an empty string
    /// from PDFKit and falls through to Vision OCR.
    private func makeImagePDF(text: String) throws -> URL {
        let pageRect = CGRect(x: 0, y: 0, width: 612, height: 200)
        let imageScale: CGFloat = 3.0
        let imageSize = CGSize(
            width: pageRect.width * imageScale,
            height: pageRect.height * imageScale
        )

        // Step 1: render text as a high-resolution raster image.
        let imageRenderer = UIGraphicsImageRenderer(size: imageSize)
        let textImage = imageRenderer.image { ctx in
            UIColor.white.setFill()
            ctx.fill(CGRect(origin: .zero, size: imageSize))
            let attrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.boldSystemFont(ofSize: 48 * imageScale),
                .foregroundColor: UIColor.black
            ]
            text.draw(at: CGPoint(x: 40 * imageScale, y: 55 * imageScale), withAttributes: attrs)
        }

        // Step 2: embed the raster image into a PDF page (no PDF text operators).
        let pdfRenderer = UIGraphicsPDFRenderer(bounds: pageRect)
        let pdfData = pdfRenderer.pdfData { ctx in
            ctx.beginPage()
            textImage.draw(in: pageRect)
        }

        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("bone-image-\(UUID().uuidString).pdf")
        try pdfData.write(to: url)
        return url
    }

    /// Creates a minimal password-protected PDF using CoreGraphics.
    /// The non-empty user password prevents PDFKit from auto-unlocking,
    /// so `isEncrypted = true` and `isUnlocked = false`.
    private func makeEncryptedPDF() throws -> URL {
        let pdfData = NSMutableData()
        guard let consumer = CGDataConsumer(data: pdfData as CFMutableData) else {
            throw NSError(domain: "BoneExtractorTests", code: 1,
                          userInfo: [NSLocalizedDescriptionKey: "CGDataConsumer creation failed"])
        }
        var mediaBox = CGRect(x: 0, y: 0, width: 200, height: 200)
        let auxInfo: [String: String] = [
            kCGPDFContextOwnerPassword as String: "ownerpass",
            kCGPDFContextUserPassword as String: "userpass"
        ]
        guard let context = CGContext(
            consumer: consumer,
            mediaBox: &mediaBox,
            auxInfo as CFDictionary
        ) else {
            throw NSError(domain: "BoneExtractorTests", code: 2,
                          userInfo: [NSLocalizedDescriptionKey: "CGContext creation failed"])
        }
        context.beginPDFPage(nil)
        context.endPDFPage()
        context.closePDF()

        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("bone-encrypted-\(UUID().uuidString).pdf")
        try (pdfData as Data).write(to: url)
        return url
    }

    private func writeTempFile(content: String, ext: String) throws -> URL {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("bone-\(UUID().uuidString).\(ext)")
        try content.write(to: url, atomically: true, encoding: .utf8)
        return url
    }
}
