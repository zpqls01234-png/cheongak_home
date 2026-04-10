import Foundation

/// App Group suite name for sharing data between main app and keyboard extension
let appGroupSuiteName = "group.com.transtype.shared"

/// Keys for UserDefaults stored in the shared App Group container
enum UserDefaultsKeys {
    static let enabledLanguages = "enabledLanguages"
    static let autoTranslateEnabled = "autoTranslateEnabled"
    static let debounceInterval = "debounceInterval"
    static let hapticFeedbackEnabled = "hapticFeedbackEnabled"

    // Default values
    static let defaultDebounceInterval: Double = 0.3
    static let defaultAutoTranslate: Bool = true
    static let defaultHapticFeedback: Bool = true
}

/// Convenience wrapper for shared UserDefaults
final class SharedSettings {
    static let shared = SharedSettings()

    private let defaults: UserDefaults

    init() {
        defaults = UserDefaults(suiteName: appGroupSuiteName) ?? .standard
        registerDefaults()
    }

    private func registerDefaults() {
        let defaultLanguages = SupportedLanguage.defaultEnabled.map { $0.rawValue }
        defaults.register(defaults: [
            UserDefaultsKeys.enabledLanguages: defaultLanguages,
            UserDefaultsKeys.autoTranslateEnabled: UserDefaultsKeys.defaultAutoTranslate,
            UserDefaultsKeys.debounceInterval: UserDefaultsKeys.defaultDebounceInterval,
            UserDefaultsKeys.hapticFeedbackEnabled: UserDefaultsKeys.defaultHapticFeedback,
        ])
    }

    // MARK: - Enabled Languages

    var enabledLanguages: Set<SupportedLanguage> {
        get {
            let rawValues = defaults.stringArray(forKey: UserDefaultsKeys.enabledLanguages) ?? []
            let languages = rawValues.compactMap { SupportedLanguage(rawValue: $0) }
            return languages.isEmpty ? SupportedLanguage.defaultEnabled : Set(languages)
        }
        set {
            let rawValues = newValue.map { $0.rawValue }
            defaults.set(rawValues, forKey: UserDefaultsKeys.enabledLanguages)
        }
    }

    // MARK: - Auto Translate

    var autoTranslateEnabled: Bool {
        get { defaults.bool(forKey: UserDefaultsKeys.autoTranslateEnabled) }
        set { defaults.set(newValue, forKey: UserDefaultsKeys.autoTranslateEnabled) }
    }

    // MARK: - Debounce Interval

    var debounceInterval: Double {
        get {
            let value = defaults.double(forKey: UserDefaultsKeys.debounceInterval)
            return value > 0 ? value : UserDefaultsKeys.defaultDebounceInterval
        }
        set { defaults.set(newValue, forKey: UserDefaultsKeys.debounceInterval) }
    }

    // MARK: - Haptic Feedback

    var hapticFeedbackEnabled: Bool {
        get { defaults.bool(forKey: UserDefaultsKeys.hapticFeedbackEnabled) }
        set { defaults.set(newValue, forKey: UserDefaultsKeys.hapticFeedbackEnabled) }
    }
}
