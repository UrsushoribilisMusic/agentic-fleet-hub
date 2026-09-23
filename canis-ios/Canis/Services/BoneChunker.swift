import Foundation

/// A single retrieval-ready unit produced by `BoneChunker.chunk(_:)`.
struct BoneChunk: Sendable, Equatable {
    /// 0-based sequential index within this chunk list.
    let index: Int
    /// Verbatim source text, approximately 300–500 tokens.
    let text: String
    /// The `ExtractedPage.pageNumber` of the first page that contributed to
    /// this chunk.  For txt/md the extractor always sets `pageNumber = 1`;
    /// for PDFs this is the 1-based page number where the chunk begins.
    let sourcePage: Int
}

/// Converts `[ExtractedPage]` from `BoneExtractor` into a flat list of
/// retrieval-ready `BoneChunk` values.
///
/// ## Algorithm (matches BONE_SPEC §3)
///
/// **Stage 1 — Pre-segmentation** (per page):
///   Split each page's text into segments on markdown heading lines
///   (`^#{1,6} `) and blank-line paragraph boundaries.
///
/// **Stage 2 — Greedy packing**:
///   Pack segments into ~400-token windows with ~60-token overlap carried
///   from the tail of the previous window.  Trailing remnants shorter than
///   50 tokens are merged into the previous chunk.
///
/// **Token estimation**: `ceil(utf8_byte_count / 4)`.  This over-counts
/// BPE subword tokens by ~10–20% for English prose, keeping windows safely
/// inside the 512-token hard cap.
///
/// **Losslessness**: every byte of source text appears in at least one
/// chunk, modulo whitespace normalisation (blank-line separators collapsed
/// to `\n\n`, leading/trailing whitespace trimmed per segment).
///
/// **Reproducibility**: the algorithm is purely functional — same input
/// produces byte-identical output on every call.
final class BoneChunker {

    // MARK: - Parameters (BONE_SPEC §2)

    /// Greedy-pack target.  Stop adding segments once the window reaches this.
    let targetTokens = 400
    /// Overlap carried from the tail of the previous window into the next.
    let overlapTokens = 60
    /// Trailing remnants shorter than this are merged into the previous chunk.
    let minChunkTokens = 50
    /// A single chunk must never exceed this.
    let hardCapTokens = 512

    // MARK: - Public API

    func chunk(_ pages: [ExtractedPage]) -> [BoneChunk] {
        let segments = presegment(pages)
        let expanded = expandOversized(segments)
        return greedyPack(expanded)
    }

    // MARK: - Token estimation

    /// Returns `ceil(utf8_byte_count / 4)`.
    func estimateTokens(_ text: String) -> Int {
        (text.utf8.count + 3) / 4
    }

    // MARK: - Pre-segmentation

    private struct Segment {
        let text: String
        /// Mirrors `ExtractedPage.pageNumber`.
        let sourcePage: Int
    }

    private func presegment(_ pages: [ExtractedPage]) -> [Segment] {
        pages.flatMap { segmentPage($0) }
    }

    /// Splits a single page into segments on heading and blank-line boundaries.
    private func segmentPage(_ page: ExtractedPage) -> [Segment] {
        var segments: [Segment] = []
        var currentLines: [String] = []

        func flush() {
            let text = currentLines
                .joined(separator: "\n")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            if !text.isEmpty {
                segments.append(Segment(text: text, sourcePage: page.pageNumber))
            }
            currentLines.removeAll()
        }

        for line in page.text.components(separatedBy: "\n") {
            if line.trimmingCharacters(in: .whitespaces).isEmpty {
                flush()
            } else if isHeadingLine(line) {
                flush()
                currentLines.append(line)
            } else {
                currentLines.append(line)
            }
        }
        flush()
        return segments
    }

    private func isHeadingLine(_ line: String) -> Bool {
        line.range(of: #"^#{1,6} "#, options: .regularExpression) != nil
    }

    // MARK: - Oversized segment expansion

    /// Splits any segment exceeding `hardCapTokens` at sentence boundaries,
    /// falling back to a hard byte-position split if no boundary is found.
    private func expandOversized(_ segments: [Segment]) -> [Segment] {
        segments.flatMap { seg -> [Segment] in
            guard estimateTokens(seg.text) > hardCapTokens else { return [seg] }
            return splitOversized(seg)
        }
    }

    private func splitOversized(_ seg: Segment) -> [Segment] {
        var result: [Segment] = []
        var remaining = seg.text

        while estimateTokens(remaining) > hardCapTokens {
            let maxBytes = hardCapTokens * 4
            // Examine only up to hardCap tokens' worth of bytes.
            let prefix = truncateToBytes(remaining, maxBytes: maxBytes)

            // Find the last sentence boundary (punctuation + whitespace → uppercase)
            // within the prefix.  Store the CHARACTER OFFSET (not a String.Index from
            // prefix) so we can safely apply it to `remaining` later.
            var bestSplitCharOffset: Int? = nil
            var searchStart = prefix.startIndex
            while searchStart < prefix.endIndex {
                guard let punctRange = prefix.range(
                    of: #"[.!?]"#,
                    options: .regularExpression,
                    range: searchStart..<prefix.endIndex
                ) else { break }
                // Skip whitespace after the punctuation mark.
                var afterPunct = punctRange.upperBound
                while afterPunct < prefix.endIndex && prefix[afterPunct].isWhitespace {
                    prefix.formIndex(after: &afterPunct)
                }
                if afterPunct < prefix.endIndex && prefix[afterPunct].isUppercase {
                    // Store the character-count offset so we can address `remaining`.
                    bestSplitCharOffset = prefix.distance(from: prefix.startIndex, to: afterPunct)
                }
                searchStart = punctRange.upperBound
            }

            if let offset = bestSplitCharOffset {
                let splitIdx = remaining.index(remaining.startIndex, offsetBy: offset)
                let part = String(remaining[..<splitIdx])
                    .trimmingCharacters(in: .whitespacesAndNewlines)
                if !part.isEmpty {
                    result.append(Segment(text: part, sourcePage: seg.sourcePage))
                }
                remaining = String(remaining[splitIdx...])
                    .trimmingCharacters(in: .whitespacesAndNewlines)
            } else {
                // No sentence boundary — hard-split at a word boundary near maxBytes.
                let splitIdx = wordBoundaryIndex(in: remaining, approxBytes: maxBytes)
                if splitIdx <= remaining.startIndex {
                    // Cannot split further; emit the rest as-is and stop.
                    result.append(Segment(text: remaining, sourcePage: seg.sourcePage))
                    return result
                }
                let part = String(remaining[..<splitIdx])
                    .trimmingCharacters(in: .whitespacesAndNewlines)
                if !part.isEmpty {
                    result.append(Segment(text: part, sourcePage: seg.sourcePage))
                }
                let rest = String(remaining[splitIdx...])
                    .trimmingCharacters(in: .whitespacesAndNewlines)
                guard !rest.isEmpty else { return result }
                remaining = rest
            }
        }

        if !remaining.isEmpty {
            result.append(Segment(text: remaining, sourcePage: seg.sourcePage))
        }
        return result
    }

    /// Truncates `text` to at most `maxBytes` UTF-8 bytes, retreating to a
    /// valid character boundary.
    private func truncateToBytes(_ text: String, maxBytes: Int) -> String {
        let bytes = Array(text.utf8)
        guard bytes.count > maxBytes else { return text }
        var end = maxBytes
        // Retreat past continuation bytes (10xxxxxx) to find a char start.
        while end > 0 && (bytes[end] & 0xC0) == 0x80 { end -= 1 }
        return String(decoding: Array(bytes[..<end]), as: UTF8.self)
    }

    /// Returns a `String.Index` approximately `approxBytes` UTF-8 bytes from
    /// the start of `text`, retreated to a word boundary.
    private func wordBoundaryIndex(in text: String, approxBytes: Int) -> String.Index {
        let bytes = Array(text.utf8)
        guard approxBytes < bytes.count else { return text.endIndex }
        var bytePos = approxBytes
        // Retreat to a valid char start.
        while bytePos > 0 && (bytes[bytePos] & 0xC0) == 0x80 { bytePos -= 1 }
        let prefix = String(decoding: Array(bytes[..<bytePos]), as: UTF8.self)
        // Retreat to the last whitespace to avoid cutting mid-word.
        var idx = prefix.endIndex
        while idx > prefix.startIndex {
            let prev = prefix.index(before: idx)
            if prefix[prev].isWhitespace { break }
            idx = prev
        }
        let charOffset = prefix.distance(from: prefix.startIndex, to: idx)
        return text.index(text.startIndex, offsetBy: charOffset)
    }

    // MARK: - Greedy packing

    private func greedyPack(_ segments: [Segment]) -> [BoneChunk] {
        guard !segments.isEmpty else { return [] }

        var chunks: [BoneChunk] = []
        var windowText = ""
        var windowTokens = 0
        var windowStartPage = 0

        func emitWindow() {
            guard !windowText.isEmpty else { return }
            chunks.append(BoneChunk(
                index: chunks.count,
                text: windowText,
                sourcePage: windowStartPage
            ))
        }

        for segment in segments {
            let segTokens = estimateTokens(segment.text)
            // +1 for the "\n\n" separator (2 bytes → 1 token).
            let projectedTokens = windowTokens + 1 + segTokens
            let wouldOverflow = !windowText.isEmpty
                && projectedTokens > targetTokens
                && windowTokens >= minChunkTokens

            if wouldOverflow {
                emitWindow()

                // Clamp overlap so overlap + separator + segment stays within hardCap.
                let overlapBudget = max(0, hardCapTokens - segTokens - 1)
                let clampedOverlap = min(overlapTokens, overlapBudget)
                let overlap = tailTokens(windowText, clampedOverlap)

                // Heading carry-forward: if the incoming segment starts with a heading,
                // put the heading line first so the LLM sees the section title at the
                // top of the new chunk, then the overlap context, then the body.
                let firstLine = segment.text.components(separatedBy: "\n").first ?? ""
                if isHeadingLine(firstLine) {
                    let bodyStart = segment.text.index(
                        segment.text.startIndex,
                        offsetBy: firstLine.count
                    )
                    let body = String(segment.text[bodyStart...])
                        .trimmingCharacters(in: .whitespacesAndNewlines)
                    windowText = firstLine
                    if !overlap.isEmpty { windowText += "\n\n" + overlap }
                    if !body.isEmpty     { windowText += "\n\n" + body }
                } else {
                    windowText = overlap.isEmpty ? segment.text : overlap + "\n\n" + segment.text
                }
                windowTokens = estimateTokens(windowText)
                windowStartPage = segment.sourcePage
            } else {
                if windowText.isEmpty {
                    windowStartPage = segment.sourcePage
                    windowText = segment.text
                } else {
                    windowText += "\n\n" + segment.text
                }
                windowTokens = estimateTokens(windowText)
            }
        }

        // Flush the final window.
        if estimateTokens(windowText) >= minChunkTokens {
            emitWindow()
        } else if !windowText.isEmpty {
            if chunks.isEmpty {
                // Entire document is shorter than minChunkTokens — emit it as-is.
                emitWindow()
            } else {
                // Merge the short tail into the previous chunk.
                let last = chunks.removeLast()
                chunks.append(BoneChunk(
                    index: last.index,
                    text: last.text + "\n\n" + windowText,
                    sourcePage: last.sourcePage
                ))
            }
        }

        return chunks
    }

    // MARK: - Tail extraction

    /// Returns the last approximately `tokenCount` tokens of `text`, aligned
    /// to a word boundary.  Used to compute the overlap region.
    private func tailTokens(_ text: String, _ tokenCount: Int) -> String {
        guard tokenCount > 0 else { return "" }
        let approxBytes = tokenCount * 4
        let bytes = Array(text.utf8)
        guard bytes.count > approxBytes else { return text }

        var startByte = bytes.count - approxBytes
        // Advance past continuation bytes to land on a char start.
        while startByte < bytes.count && (bytes[startByte] & 0xC0) == 0x80 {
            startByte += 1
        }
        let tail = String(decoding: Array(bytes[startByte...]), as: UTF8.self)

        // Skip past any partial word so the overlap starts at a clean boundary.
        var idx = tail.startIndex
        while idx < tail.endIndex && !tail[idx].isWhitespace {
            tail.formIndex(after: &idx)
        }
        while idx < tail.endIndex && tail[idx].isWhitespace {
            tail.formIndex(after: &idx)
        }
        return String(tail[idx...])
    }
}
