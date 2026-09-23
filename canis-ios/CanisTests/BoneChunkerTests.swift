import XCTest
@testable import Canis

final class BoneChunkerTests: XCTestCase {
    private let chunker = BoneChunker()

    // MARK: - Helpers

    /// Builds a minimal [ExtractedPage] from a string (txt/md — no page tracking).
    private func pages(_ text: String) -> [ExtractedPage] {
        [ExtractedPage(pageNumber: 1, text: text)]
    }

    /// Builds one ExtractedPage per string, simulating a multi-page PDF.
    private func pdfPages(_ texts: [String]) -> [ExtractedPage] {
        texts.enumerated().map { ExtractedPage(pageNumber: $0.offset + 1, text: $0.element) }
    }

    /// Generates a paragraph of at least `minTokens` estimated tokens.
    private func paragraph(tokens minTokens: Int) -> String {
        // Each "word " is ~5 bytes → ~1.25 tokens.  Multiply to overshoot safely.
        let wordCount = (minTokens * 4) / 5 + 10
        return (0..<wordCount).map { "word\($0)" }.joined(separator: " ")
    }

    // MARK: - (a) Determinism

    func testDeterministicOutputOnIdenticalInput() {
        let text = """
        ## Introduction
        This is the first paragraph of the document.

        It contains multiple paragraphs so the chunker has something to work with.

        ## Body
        Here is more content with enough text to potentially produce multiple chunks.
        """
        let input = pages(text)
        let first = chunker.chunk(input)
        let second = chunker.chunk(input)

        XCTAssertEqual(first.map(\.text), second.map(\.text),
                       "Same input must produce byte-identical chunk text")
        XCTAssertEqual(first.map(\.sourcePage), second.map(\.sourcePage),
                       "Same input must produce identical source pages")
        XCTAssertEqual(first.map(\.index), second.map(\.index))
    }

    func testDeterministicAcrossMultiplePages() {
        let input = pdfPages([
            "Page one content. " + paragraph(tokens: 200),
            "Page two content. " + paragraph(tokens: 200),
        ])
        XCTAssertEqual(
            chunker.chunk(input).map(\.text),
            chunker.chunk(input).map(\.text)
        )
    }

    // MARK: - (b) Token bounds

    func testAllChunksWithinTokenBounds() {
        // Feed enough content to produce multiple chunks.
        let text = (0..<20).map { "## Section \($0)\n" + paragraph(tokens: 80) }
            .joined(separator: "\n\n")
        let chunks = chunker.chunk(pages(text))

        XCTAssertFalse(chunks.isEmpty)
        for c in chunks {
            let t = chunker.estimateTokens(c.text)
            XCTAssertLessThanOrEqual(t, chunker.hardCapTokens,
                "Chunk \(c.index) has \(t) tokens > hardCap \(chunker.hardCapTokens)")
        }
    }

    func testChunksAboveMinTokensExceptPossibleLast() {
        let text = (0..<10).map { "## Section \($0)\n" + paragraph(tokens: 80) }
            .joined(separator: "\n\n")
        let chunks = chunker.chunk(pages(text))

        // All chunks except possibly the last (could be merged remnant) should
        // meet the min — but after merging, even the last should be ≥ min.
        for c in chunks {
            let t = chunker.estimateTokens(c.text)
            XCTAssertGreaterThanOrEqual(t, chunker.minChunkTokens,
                "Chunk \(c.index) has only \(t) tokens (min = \(chunker.minChunkTokens))")
        }
    }

    // MARK: - (c) Overlap

    func testConsecutiveChunksShareContent() {
        let text = (0..<12).map { "## Section \($0)\n" + paragraph(tokens: 100) }
            .joined(separator: "\n\n")
        let chunks = chunker.chunk(pages(text))

        guard chunks.count >= 2 else {
            XCTFail("Expected at least 2 chunks, got \(chunks.count)")
            return
        }

        for i in 0..<(chunks.count - 1) {
            let current = chunks[i].text
            let next = chunks[i + 1].text

            // Extract the last ~overlapTokens worth of words from `current`
            // and verify at least one substantial word appears in `next`.
            let tailWords = tailWords(of: current, approxTokens: chunker.overlapTokens * 2)
            let nextWords = Set(next.components(separatedBy: .whitespacesAndNewlines)
                .filter { $0.count > 3 })

            let shared = tailWords.filter { nextWords.contains($0) }
            XCTAssertFalse(shared.isEmpty,
                "Chunks \(i) and \(i+1) share no overlap words. " +
                "End of chunk \(i): …\(String(current.suffix(100)))\n" +
                "Start of chunk \(i+1): \(String(next.prefix(100)))…")
        }
    }

    private func tailWords(of text: String, approxTokens: Int) -> Set<String> {
        let approxChars = approxTokens * 4
        let suffix = approxChars < text.count
            ? String(text.suffix(approxChars))
            : text
        return Set(suffix.components(separatedBy: .whitespacesAndNewlines)
            .filter { $0.count > 3 })
    }

    // MARK: - (d) Losslessness

    func testEverySegmentAppearsInAtLeastOneChunk() {
        let sections = (0..<8).map {
            "## Section \($0)\nThis is section \($0) body text with enough content to matter."
        }
        let text = sections.joined(separator: "\n\n")
        let input = pages(text)
        let chunks = chunker.chunk(input)
        let combinedChunks = chunks.map(\.text).joined(separator: " ")

        // Each distinct word from the original must appear somewhere in the chunks.
        let sourceWords = Set(text.components(separatedBy: .whitespacesAndNewlines)
            .filter { !$0.isEmpty })
        let chunkWords = Set(combinedChunks.components(separatedBy: .whitespacesAndNewlines)
            .filter { !$0.isEmpty })

        let missing = sourceWords.subtracting(chunkWords)
        XCTAssertTrue(missing.isEmpty,
            "Words from source missing in chunks: \(missing.prefix(10))")
    }

    func testMultiPageLosslessness() {
        let pageTexts = (0..<5).map { "Page \($0) content. " + paragraph(tokens: 120) }
        let input = pdfPages(pageTexts)
        let chunks = chunker.chunk(input)
        let combinedChunks = chunks.map(\.text).joined(separator: " ")

        for (i, pageText) in pageTexts.enumerated() {
            let pageWords = pageText.components(separatedBy: .whitespaces).filter { !$0.isEmpty }
            for word in pageWords {
                XCTAssertTrue(combinedChunks.contains(word),
                    "Word '\(word)' from page \(i+1) not found in any chunk")
            }
        }
    }

    // MARK: - (e) Source page tracking

    func testTxtInputSourcePageMirrorsPageNumber() {
        // BoneExtractor sets pageNumber=1 for txt/md; BoneChunker passes it through.
        let chunks = chunker.chunk(pages(paragraph(tokens: 200)))
        XCTAssertFalse(chunks.isEmpty)
        for c in chunks {
            XCTAssertEqual(c.sourcePage, 1,
                "Chunk \(c.index) should carry sourcePage=1 from the single txt page")
        }
    }

    func testPDFSourcePageReflectsChunkStartPage() {
        // Page 1 is short; page 2 has enough content to force a new chunk.
        let input = pdfPages([
            "Short page one paragraph.",
            paragraph(tokens: 450),
        ])
        let chunks = chunker.chunk(input)
        XCTAssertFalse(chunks.isEmpty)
        // The first chunk should begin on page 1.
        XCTAssertEqual(chunks[0].sourcePage, 1)
        // At least one chunk should reflect page 2.
        let hasPage2 = chunks.contains { $0.sourcePage == 2 }
        XCTAssertTrue(hasPage2, "No chunk carries sourcePage=2 after a 450-token page")
    }

    // MARK: - (f) Edge cases

    func testEmptyInputProducesNoChunks() {
        XCTAssertTrue(chunker.chunk([]).isEmpty)
    }

    func testEmptyPageTextProducesNoChunks() {
        let input = [ExtractedPage(pageNumber: 1, text: "   \n\n   ")]
        XCTAssertTrue(chunker.chunk(input).isEmpty)
    }

    func testShortDocumentBelowMinTokensIsEmittedAsSingleChunk() {
        let short = "Hello, world."
        let chunks = chunker.chunk(pages(short))
        XCTAssertEqual(chunks.count, 1)
        XCTAssertTrue(chunks[0].text.contains("Hello"))
    }

    func testSingleVeryLongParagraphIsHardCapped() {
        // A single paragraph well over 512 tokens.
        let longPara = paragraph(tokens: 700)
        let chunks = chunker.chunk(pages(longPara))
        XCTAssertFalse(chunks.isEmpty)
        for c in chunks {
            XCTAssertLessThanOrEqual(
                chunker.estimateTokens(c.text), chunker.hardCapTokens,
                "Chunk \(c.index) exceeds hardCap")
        }
    }

    func testChunkIndicesAreContiguousFromZero() {
        let text = (0..<12).map { "## S\($0)\n" + paragraph(tokens: 100) }
            .joined(separator: "\n\n")
        let chunks = chunker.chunk(pages(text))
        for (i, c) in chunks.enumerated() {
            XCTAssertEqual(c.index, i, "Chunk at position \(i) has index \(c.index)")
        }
    }

    func testHeadingCarryForward() {
        // The heading should appear in the chunk it starts, even after a split.
        let heading = "## Important Section"
        // Large preamble forces a split before the heading.
        let preamble = paragraph(tokens: 420)
        let body = paragraph(tokens: 80)
        let text = preamble + "\n\n" + heading + "\n" + body

        let chunks = chunker.chunk(pages(text))
        // Find the chunk that contains the heading.
        let headingChunk = chunks.first { $0.text.contains("Important Section") }
        XCTAssertNotNil(headingChunk, "No chunk contains the heading '## Important Section'")
    }
}
