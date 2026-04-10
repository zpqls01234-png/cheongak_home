import SwiftUI

/// Main content view with settings, language toggles, and test input field
struct ContentView: View {

    // MARK: - State

    @State private var settings = SharedSettings.shared

    // Language toggles
    @State private var englishEnabled: Bool
    @State private var japaneseEnabled: Bool
    @State private var chineseEnabled: Bool
    @State private var spanishEnabled: Bool

    // Settings
    @State private var autoTranslateEnabled: Bool
    @State private var debounceInterval: Double
    @State private var hapticEnabled: Bool

    // Test input
    @State private var testInputText: String = ""
    @State private var translationHistory: [HistoryEntry] = []

    init() {
        let s = SharedSettings.shared
        let langs = s.enabledLanguages
        _englishEnabled = State(initialValue: langs.contains(.english))
        _japaneseEnabled = State(initialValue: langs.contains(.japanese))
        _chineseEnabled = State(initialValue: langs.contains(.chinese))
        _spanishEnabled = State(initialValue: langs.contains(.spanish))
        _autoTranslateEnabled = State(initialValue: s.autoTranslateEnabled)
        _debounceInterval = State(initialValue: s.debounceInterval)
        _hapticEnabled = State(initialValue: s.hapticFeedbackEnabled)
    }

    var body: some View {
        List {
            // Section 1: Keyboard Setup
            keyboardSetupSection

            // Section 2: Language Settings
            languageSection

            // Section 3: Translation Settings
            translationSettingsSection

            // Section 4: Test Input
            testInputSection

            // Section 5: About
            aboutSection
        }
        .navigationTitle("TransType")
        .onChange(of: englishEnabled) { syncLanguages() }
        .onChange(of: japaneseEnabled) { syncLanguages() }
        .onChange(of: chineseEnabled) { syncLanguages() }
        .onChange(of: spanishEnabled) { syncLanguages() }
        .onChange(of: autoTranslateEnabled) {
            settings.autoTranslateEnabled = autoTranslateEnabled
        }
        .onChange(of: debounceInterval) {
            settings.debounceInterval = debounceInterval
        }
        .onChange(of: hapticEnabled) {
            settings.hapticFeedbackEnabled = hapticEnabled
        }
    }

    // MARK: - Keyboard Setup Section

    private var keyboardSetupSection: some View {
        Section {
            NavigationLink {
                OnboardingView()
            } label: {
                HStack(spacing: 12) {
                    Image(systemName: "keyboard")
                        .font(.title2)
                        .foregroundStyle(.blue)
                        .frame(width: 36)

                    VStack(alignment: .leading, spacing: 2) {
                        Text("키보드 설정 가이드")
                            .font(.subheadline)
                            .fontWeight(.medium)
                        Text("키보드 활성화 및 전체 접근 허용 안내")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 4)
            }
        } header: {
            Text("키보드 설정")
        } footer: {
            Text("TransType 키보드를 사용하려면 먼저 설정에서 활성화해야 합니다.")
        }
    }

    // MARK: - Language Section

    private var languageSection: some View {
        Section {
            languageToggle(
                flag: "🇺🇸",
                name: "영어 (English)",
                isOn: $englishEnabled,
                isOnly: onlyOneEnabled && englishEnabled
            )
            languageToggle(
                flag: "🇯🇵",
                name: "일본어 (日本語)",
                isOn: $japaneseEnabled,
                isOnly: onlyOneEnabled && japaneseEnabled
            )
            languageToggle(
                flag: "🇨🇳",
                name: "중국어 (中文)",
                isOn: $chineseEnabled,
                isOnly: onlyOneEnabled && chineseEnabled
            )
            languageToggle(
                flag: "🇪🇸",
                name: "스페인어 (Español)",
                isOn: $spanishEnabled,
                isOnly: onlyOneEnabled && spanishEnabled
            )
        } header: {
            Text("번역 대상 언어")
        } footer: {
            Text("선택한 언어로 한국어 입력을 실시간 번역합니다. 최소 1개 언어는 활성화되어야 합니다.")
        }
    }

    private func languageToggle(flag: String, name: String, isOn: Binding<Bool>, isOnly: Bool) -> some View {
        Toggle(isOn: isOn) {
            HStack(spacing: 8) {
                Text(flag)
                    .font(.title3)
                Text(name)
                    .font(.subheadline)
            }
        }
        .disabled(isOnly) // Prevent disabling the last enabled language
    }

    /// Whether only one language is currently enabled
    private var onlyOneEnabled: Bool {
        let count = [englishEnabled, japaneseEnabled, chineseEnabled, spanishEnabled]
            .filter { $0 }.count
        return count <= 1
    }

    // MARK: - Translation Settings Section

    private var translationSettingsSection: some View {
        Section {
            Toggle(isOn: $autoTranslateEnabled) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("자동 번역")
                        .font(.subheadline)
                    Text("한국어 입력 시 자동으로 번역을 시작합니다")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("디바운스 간격")
                        .font(.subheadline)
                    Spacer()
                    Text(String(format: "%.1f초", debounceInterval))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .monospacedDigit()
                }
                Slider(value: $debounceInterval, in: 0.1...1.0, step: 0.1)
                    .tint(.blue)
                Text("타이핑 후 번역이 시작되기까지의 대기 시간입니다")
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
            .padding(.vertical, 4)

            Toggle(isOn: $hapticEnabled) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("햅틱 피드백")
                        .font(.subheadline)
                    Text("번역 선택 시 가벼운 진동 피드백을 줍니다")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        } header: {
            Text("번역 설정")
        }
    }

    // MARK: - Test Input Section

    private var testInputSection: some View {
        Section {
            VStack(alignment: .leading, spacing: 12) {
                Text("아래 입력 필드에서 TransType 키보드를 테스트해보세요.")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                TextField("한국어를 입력해보세요...", text: $testInputText, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(3...6)
                    .font(.body)

                if !testInputText.isEmpty {
                    Button("테스트 번역") {
                        performTestTranslation()
                    }
                    .font(.subheadline)
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding(.vertical, 4)

            // Translation history
            if !translationHistory.isEmpty {
                ForEach(translationHistory) { entry in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(entry.sourceText)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        ForEach(entry.translations, id: \.language) { result in
                            HStack(spacing: 4) {
                                Text(result.language.flagEmoji)
                                    .font(.caption)
                                Text(result.translatedText)
                                    .font(.subheadline)
                                    .fontWeight(.medium)
                            }
                        }
                    }
                    .padding(.vertical, 2)
                }

                Button("기록 삭제", role: .destructive) {
                    translationHistory.removeAll()
                }
                .font(.caption)
            }
        } header: {
            Text("테스트")
        } footer: {
            Text("TransType 키보드로 전환한 후 한국어를 입력하면 상단에 번역 결과가 표시됩니다.")
        }
    }

    // MARK: - About Section

    private var aboutSection: some View {
        Section {
            HStack {
                Text("버전")
                    .font(.subheadline)
                Spacer()
                Text("1.0.0")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            HStack {
                Text("지원 언어")
                    .font(.subheadline)
                Spacer()
                Text("한국어 → 영어, 일본어")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        } header: {
            Text("정보")
        }
    }

    // MARK: - Actions

    private func syncLanguages() {
        var langs = Set<SupportedLanguage>()
        if englishEnabled { langs.insert(.english) }
        if japaneseEnabled { langs.insert(.japanese) }
        if chineseEnabled { langs.insert(.chinese) }
        if spanishEnabled { langs.insert(.spanish) }

        // Ensure at least one language is enabled
        if langs.isEmpty {
            langs.insert(.english)
            englishEnabled = true
        }

        settings.enabledLanguages = langs
    }

    private func performTestTranslation() {
        let service = TranslationService()
        let text = testInputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }

        // Split into words and translate each Korean word
        let words = text.components(separatedBy: .whitespaces).filter { !$0.isEmpty }
        var allResults: [TranslationResult] = []

        for word in words where TranslationService.isKorean(word) {
            service.onTranslationsReady = { results in
                allResults.append(contentsOf: results)
            }
            service.translate(text: word)
        }

        // Since the service uses debounce, we wait and then collect results
        // For the test screen, we use the dictionary directly
        let enabledLangs = settings.enabledLanguages
        var testResults: [TranslationResult] = []

        for word in words where TranslationService.isKorean(word) {
            // Direct dictionary lookup for test purposes
            let service = TranslationService()
            service.onTranslationsReady = { results in
                testResults.append(contentsOf: results)

                // Add to history when results are received
                if !testResults.isEmpty {
                    let entry = HistoryEntry(
                        sourceText: text,
                        translations: testResults
                    )
                    translationHistory.insert(entry, at: 0)
                    // Keep only last 10 entries
                    if translationHistory.count > 10 {
                        translationHistory = Array(translationHistory.prefix(10))
                    }
                }
            }
            service.translate(text: word)
        }
    }
}

// MARK: - History Entry

private struct HistoryEntry: Identifiable {
    let id = UUID()
    let sourceText: String
    let translations: [TranslationResult]
}

#Preview {
    NavigationStack {
        ContentView()
    }
}
