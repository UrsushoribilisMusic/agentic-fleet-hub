import SwiftUI

struct RootView: View {
    @AppStorage("canis.activeModelID") private var activeModelID = CanisModel.apertus.rawValue
    @EnvironmentObject private var ingestion: BoneIngestionManager

    var body: some View {
        TabView {
            ChatView(activeModelID: $activeModelID)
                .tabItem {
                    Label("Chat", systemImage: "message")
                }

            BoneListView()
                .tabItem {
                    Label("Bones", systemImage: "books.vertical")
                }

            ModelHubView(activeModelID: $activeModelID)
                .tabItem {
                    Label("Models", systemImage: "square.and.arrow.down")
                }
        }
        .sheet(isPresented: $ingestion.isShowingImport) {
            GiveABoneView()
                .environmentObject(ingestion)
        }
    }
}

#Preview {
    RootView()
        .environmentObject(ModelDownloadManager.shared)
        .environmentObject(KnowledgePackStore.shared)
        .environmentObject(BoneIngestionManager.shared)
}
