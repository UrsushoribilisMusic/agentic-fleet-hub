import SQLite3
import XCTest
@testable import Canis

final class BoneEnricherTests: XCTestCase {

    // MARK: - Helpers

    private let builder = BoneBuilder()

    // Fresh instance per test — prevents shared-singleton state leakage.
    private var enricher: BoneEnricher!

    override func setUp() async throws {
        try await super.setUp()
        enricher = BoneEnricher()
    }

    private func makeChunks(_ items: [(text: String, page: Int)]) -> [BoneChunk] {
        items.enumerated().map { i, p in BoneChunk(index: i, text: p.text, sourcePage: p.page) }
    }

    private func titles(in url: URL) -> [String] {
        var db: OpaquePointer?
        guard sqlite3_open_v2(url.path, &db, SQLITE_OPEN_READONLY | SQLITE_OPEN_FULLMUTEX, nil) == SQLITE_OK,
              let db else { return [] }
        defer { sqlite3_close(db) }
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, "SELECT title FROM wiki_sections ORDER BY section_index ASC", -1, &stmt, nil) == SQLITE_OK,
              let stmt else { return [] }
        defer { sqlite3_finalize(stmt) }
        var result: [String] = []
        while sqlite3_step(stmt) == SQLITE_ROW {
            result.append(sqlite3_column_text(stmt, 0).map { String(cString: $0) } ?? "")
        }
        return result
    }

    /// Waits until enrichment finishes, then drains any pending `onProgress` tasks.
    private func waitForEnrichment() async {
        while await enricher.isRunning {
            try? await Task.sleep(nanoseconds: 10_000_000)
        }
        // Allow inner progress-callback Tasks to complete.
        try? await Task.sleep(nanoseconds: 30_000_000)
    }

    // MARK: - (a) Enrichment writes non-default titles

    func testEnrichmentUpdatesTitles() async throws {
        let chunks = makeChunks([
            ("The pump calibration is a 20-minute process.", 1),
            ("Red wrench tightens bolts during arm assembly.", 2),
        ])
        let url = try builder.build(chunks: chunks, docTitle: "Robot Manual", sourceName: "rm.txt")
        defer { try? FileManager.default.removeItem(at: url) }

        let defaultTitles = titles(in: url)
        XCTAssertEqual(defaultTitles, ["Robot Manual - p.1", "Robot Manual - p.2"])

        var counter = 0
        await enricher.enrich(
            boneURL: url,
            model: .apertus,
            onProgress: { _, _ in },
            titleGenerator: { _, _ in
                counter += 1
                return "Generated \(counter)"
            }
        )
        await waitForEnrichment()

        let enriched = titles(in: url)
        XCTAssertEqual(enriched.count, 2)
        for t in enriched {
            XCTAssertFalse(t.hasPrefix("Robot Manual - p."),
                           "Expected enriched title, got default: \(t)")
        }
    }

    // MARK: - (b) Progress reporting

    func testProgressReportedCorrectly() async throws {
        let chunks = makeChunks([("A", 1), ("B", 2), ("C", 3)])
        let url = try builder.build(chunks: chunks, docTitle: "Progress Test", sourceName: "p.txt")
        defer { try? FileManager.default.removeItem(at: url) }

        let log = ProgressLog()
        await enricher.enrich(
            boneURL: url,
            model: .apertus,
            onProgress: { c, t in Task { await log.record(c, t) } },
            titleGenerator: { _, _ in "Short Title" }
        )
        await waitForEnrichment()

        let calls = await log.values
        XCTAssertEqual(calls.count, 3, "onProgress should fire once per chunk")
        XCTAssertEqual(calls.last?.1, 3, "total should equal chunk count")
        for (i, (completed, total)) in calls.enumerated() {
            XCTAssertEqual(completed, i + 1, "completed should increment")
            XCTAssertEqual(total, 3, "total should be stable")
        }
    }

    // MARK: - (c) Cancel stops early

    func testCancelStopsEarly() async throws {
        let n = 10
        let chunks = makeChunks((0..<n).map { ("Chunk \($0) body text.", 1) })
        let url = try builder.build(chunks: chunks, docTitle: "Cancel Test", sourceName: "c.txt")
        defer { try? FileManager.default.removeItem(at: url) }

        let log = ProgressLog()
        await enricher.enrich(
            boneURL: url,
            model: .apertus,
            onProgress: { c, _ in Task { await log.record(c, 0) } },
            titleGenerator: { _, _ in
                try await Task.sleep(nanoseconds: 10_000_000)  // 10 ms per chunk
                return "Title"
            }
        )
        // Cancel after some chunks have started but before all finish
        try await Task.sleep(nanoseconds: 25_000_000)  // ~2-3 chunks in 25 ms
        await enricher.cancel()
        await waitForEnrichment()

        let count = await log.values.count
        XCTAssertLessThan(count, n, "Cancel should stop before all \(n) chunks; got \(count)")
        let notRunning = await enricher.isRunning
        XCTAssertFalse(notRunning, "isRunning should be false after cancel")
    }

    // MARK: - (d) Empty bone is a no-op

    func testEmptyBoneEnrichesWithNoErrors() async throws {
        let url = try builder.build(chunks: [], docTitle: "Empty", sourceName: "e.txt")
        defer { try? FileManager.default.removeItem(at: url) }

        let log = ProgressLog()
        await enricher.enrich(
            boneURL: url,
            model: .apertus,
            onProgress: { c, t in Task { await log.record(c, t) } },
            titleGenerator: { _, _ in "Title" }
        )
        await waitForEnrichment()

        let calls = await log.values
        XCTAssertTrue(calls.isEmpty, "No progress callbacks for an empty bone")
    }

    // MARK: - (e) isRunning toggles correctly

    func testIsRunningToggles() async throws {
        let chunks = makeChunks([("Body text for running test.", 1)])
        let url = try builder.build(chunks: chunks, docTitle: "Running Test", sourceName: "r.txt")
        defer { try? FileManager.default.removeItem(at: url) }

        // Signal: generator has started and is still running (sleeping 100 ms)
        let genStarted = AsyncFlag()
        await enricher.enrich(
            boneURL: url,
            model: .apertus,
            onProgress: { _, _ in },
            titleGenerator: { _, _ in
                await genStarted.signal()
                try await Task.sleep(nanoseconds: 100_000_000)  // keep running long enough
                return "Title"
            }
        )
        await genStarted.wait()
        let runningDuring = await enricher.isRunning

        await waitForEnrichment()
        let runningAfter = await enricher.isRunning

        XCTAssertTrue(runningDuring,  "isRunning should be true while enriching")
        XCTAssertFalse(runningAfter, "isRunning should be false after enrichment completes")
    }

    // MARK: - (f) Enriched titles load correctly via retriever

    func testEnrichedTitlesAreUsedByRetriever() async throws {
        let chunks = makeChunks([
            ("Pump calibration takes twenty minutes for torque correction.", 1),
            ("Servo motor draws 2.4 amps at peak load.", 2),
        ])
        let url = try builder.build(chunks: chunks, docTitle: "Motor Guide", sourceName: "mg.txt")
        defer { try? FileManager.default.removeItem(at: url) }

        await enricher.enrich(
            boneURL: url,
            model: .apertus,
            onProgress: { _, _ in },
            titleGenerator: { body, _ in
                if body.contains("calibration") { return "pump calibration torque" }
                return "servo motor peak load"
            }
        )
        await waitForEnrichment()

        let retrieval = try KnowledgePackRetriever(packURL: url)
            .retrieve(question: "pump calibration torque")
        XCTAssertFalse(retrieval.hits.isEmpty, "Retriever should return hits using enriched titles")
        let topTitle = retrieval.hits[0].title
        XCTAssertTrue(
            topTitle.contains("calibration") || topTitle.contains("pump"),
            "Top hit should have the enriched calibration title; got \(topTitle)"
        )
    }

    // MARK: - (g) Calling enrich twice cancels the first pass

    func testSecondEnrichCancelsPreviousPass() async throws {
        let chunks = makeChunks((0..<5).map { ("Body \($0).", 1) })
        let url = try builder.build(chunks: chunks, docTitle: "Double Test", sourceName: "d.txt")
        defer { try? FileManager.default.removeItem(at: url) }

        // First pass: slow generator
        let firstLog = ProgressLog()
        await enricher.enrich(
            boneURL: url,
            model: .apertus,
            onProgress: { c, _ in Task { await firstLog.record(c, 0) } },
            titleGenerator: { _, _ in
                try await Task.sleep(nanoseconds: 200_000_000)  // 200 ms per chunk
                return "First"
            }
        )

        // Small pause to let the first chunk start
        try await Task.sleep(nanoseconds: 20_000_000)

        // Second pass: fast generator, immediately cancels the first
        let secondLog = ProgressLog()
        await enricher.enrich(
            boneURL: url,
            model: .apertus,
            onProgress: { c, _ in Task { await secondLog.record(c, 0) } },
            titleGenerator: { _, _ in "Second" }
        )
        await waitForEnrichment()

        let firstCount  = await firstLog.values.count
        let secondCount = await secondLog.values.count

        XCTAssertEqual(secondCount, 5, "Second pass should complete all chunks; got \(secondCount)")
        XCTAssertLessThan(firstCount, 5, "First pass should have been cancelled; got \(firstCount)")
    }
}

// MARK: - Test helpers

private actor ProgressLog {
    private var _values: [(Int, Int)] = []
    var values: [(Int, Int)] { _values }
    func record(_ c: Int, _ t: Int) { _values.append((c, t)) }
}

/// Async one-shot flag: signal() once, wait() blocks until signalled.
private actor AsyncFlag {
    private var signalled = false
    private var waiters: [CheckedContinuation<Void, Never>] = []

    func signal() {
        guard !signalled else { return }
        signalled = true
        for w in waiters { w.resume() }
        waiters.removeAll()
    }

    func wait() async {
        if signalled { return }
        await withCheckedContinuation { (cont: CheckedContinuation<Void, Never>) in
            waiters.append(cont)
        }
    }
}
