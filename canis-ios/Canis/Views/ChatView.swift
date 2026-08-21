import SwiftUI

struct ChatView: View {
    @EnvironmentObject private var downloads: ModelDownloadManager
    @Binding var activeModelID: String
    @StateObject private var viewModel = ChatViewModel()

    private var activeModel: CanisModel {
        CanisModel(rawValue: activeModelID) ?? .apertus
    }

    private var selectedDownloaded: Bool {
        downloads.states[activeModel.rawValue]?.isDownloaded == true
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                modelSelector
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(.thinMaterial)

                DispositionAvatarView(readout: viewModel.currentReadout)
                    .padding(.horizontal, 16)
                    .padding(.top, 12)

                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            ForEach(viewModel.messages) { message in
                                MessageBubbleView(message: message)
                                    .id(message.id)
                            }
                        }
                        .padding(16)
                    }
                    .onChange(of: viewModel.messages) { _, messages in
                        guard let last = messages.last else { return }
                        withAnimation(.easeOut(duration: 0.2)) {
                            proxy.scrollTo(last.id, anchor: .bottom)
                        }
                    }
                }

                if !selectedDownloaded {
                    Label("Download \(activeModel.displayName) before chatting.", systemImage: "arrow.down.circle")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.bottom, 8)
                }

                composer
                    .padding(12)
                    .background(.thinMaterial)
            }
            .navigationTitle("Canis")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        viewModel.clear()
                    } label: {
                        Image(systemName: "trash")
                    }
                    .disabled(viewModel.isStreaming)
                    .accessibilityLabel("Clear chat")
                }
            }
        }
    }

    private var modelSelector: some View {
        Picker("Model", selection: $activeModelID) {
            ForEach(CanisModel.allCases) { model in
                Text(model.displayName).tag(model.rawValue)
            }
        }
        .pickerStyle(.segmented)
    }

    private var composer: some View {
        VStack(spacing: 6) {
            // CANIS-D: searching activity indicator — shown between Pass 1 and Pass 2
            if viewModel.isSearching {
                HStack(spacing: 6) {
                    ProgressView()
                        .scaleEffect(0.75)
                    Text("Searching the web…")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    if let q = viewModel.searchQuery {
                        Text(""\(q)"")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .truncationMode(.tail)
                    }
                    Spacer()
                    Text("Query sent to Brave Search")
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
                .padding(.horizontal, 4)
                .transition(.opacity.combined(with: .move(edge: .bottom)))
            }

            // CANIS-D: web search toggle + disclosure
            HStack {
                Toggle(isOn: $viewModel.webSearchEnabled) {
                    Label("Web Search", systemImage: viewModel.webSearchEnabled ? "globe.badge.chevron.backward" : "globe")
                        .font(.caption)
                        .foregroundStyle(viewModel.webSearchEnabled ? .primary : .secondary)
                }
                .toggleStyle(.button)
                .buttonStyle(.borderless)
                .tint(.blue)
                .accessibilityLabel("Toggle web search (sends query to Brave Search)")

                Spacer()
            }
            .padding(.horizontal, 4)

            HStack(alignment: .bottom, spacing: 10) {
                TextField("Ask \(activeModel.displayName)", text: $viewModel.draft, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(1...4)
                    .disabled(viewModel.isStreaming || !selectedDownloaded)

                if viewModel.isStreaming {
                    Button {
                        viewModel.stop()
                    } label: {
                        Image(systemName: "stop.fill")
                            .frame(width: 32, height: 32)
                    }
                    .buttonStyle(.bordered)
                    .accessibilityLabel("Stop generation")
                } else {
                    Button {
                        viewModel.send(using: activeModel)
                    } label: {
                        Image(systemName: "arrow.up")
                            .font(.headline)
                            .frame(width: 32, height: 32)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!selectedDownloaded || viewModel.draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    .accessibilityLabel("Send")
                }
            }
        }
    }
}
