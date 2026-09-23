# CANIS-BONE-01 Worklog

Task: Add BoneExtractor.swift — on-device text extraction (PDFKit + Vision OCR fallback)

## Plan

1. Add `Canis/Services/BoneExtractor.swift`
   - `ExtractedPage` struct with `{pageNumber, text}`
   - `BoneExtractorError` enum: `.encryptedPDF`, `.corruptPDF`, `.unsupportedFileType`, `.readFailed`
   - `BoneExtractor.extract(_ url: URL) throws -> [ExtractedPage]`
   - PDF path: PDFKit `PDFDocument` → `page.string`; if page text < threshold (scanned/image page) → Vision `VNRecognizeTextRequest` OCR (`.accurate`)
   - txt/md path: `String(contentsOf:encoding:.utf8)` → single page
   - Encrypted/corrupt: throw typed errors
   - Add comment noting reading-order limitation for tables/multi-column layouts

2. Add `CanisTests/BoneExtractorTests.swift`
   - (a) Text PDF: `UIGraphicsPDFRenderer` with drawn text → verify PDFKit extracts all pages
   - (b) Scanned/image PDF: render text → `UIGraphicsImageRenderer` raster → embed in PDF → verify OCR path fires
   - (c) .md file: write string to temp file → verify single page roundtrip
   - Determinism tests for (a) and (b)
   - Error tests: corrupt PDF, encrypted PDF, unsupported extension

3. Update `project.yml` — add PDFKit.framework and Vision.framework as explicit SDK dependencies

4. Build verify: `xcodegen generate && xcodebuild -scheme Canis -destination 'platform=iOS Simulator,name=iPhone 17' build`

## Status
- [x] BoneExtractor.swift — `Canis/Services/BoneExtractor.swift`
- [x] BoneExtractorTests.swift — `CanisTests/BoneExtractorTests.swift`
- [x] project.yml updated — PDFKit.framework + Vision.framework added
- [x] BUILD SUCCEEDED (xcodegen generate && xcodebuild -scheme Canis -destination 'platform=iOS Simulator,name=iPhone 17' build)
