import SwiftUI
import UIKit

final class AppDelegate: NSObject, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        handleEventsForBackgroundURLSession identifier: String,
        completionHandler: @escaping () -> Void
    ) {
        Task { await ModelDownloadManager.shared.handleBackgroundEvent(identifier: identifier, completionHandler: completionHandler) }
    }

    func applicationDidReceiveMemoryWarning(_ application: UIApplication) {
        Task { await CanisMLXEngine.shared.handleMemoryPressure() }
    }
}

@main
struct CanisApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var downloads = ModelDownloadManager.shared
    @StateObject private var knowledgePacks = KnowledgePackStore.shared
    @StateObject private var ingestion = BoneIngestionManager.shared
    @AppStorage("canis.activeModelID") private var activeModelID = CanisModel.apertus.rawValue

    init() {
        Task { await ModelDownloadManager.shared.setup() }
        KnowledgePackStore.shared.setup()
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(downloads)
                .environmentObject(knowledgePacks)
                .environmentObject(ingestion)
                .onOpenURL { url in
                    // Handle files shared via "Open with Canis" from Files / share sheet.
                    let model = CanisModel(rawValue: activeModelID) ?? .apertus
                    ingestion.ingest(url: url, model: model)
                    ingestion.isShowingImport = true
                }
        }
    }
}
