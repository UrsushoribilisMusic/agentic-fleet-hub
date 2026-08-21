import SwiftUI

struct RootView: View {
    @AppStorage("canis.activeModelID") private var activeModelID = CanisModel.apertus.rawValue

    var body: some View {
        TabView {
            ChatView(activeModelID: $activeModelID)
                .tabItem {
                    Label("Chat", systemImage: "message")
                }

            ModelHubView(activeModelID: $activeModelID)
                .tabItem {
                    Label("Models", systemImage: "square.and.arrow.down")
                }
        }
    }
}

#Preview {
    RootView()
        .environmentObject(ModelDownloadManager.shared)
}
