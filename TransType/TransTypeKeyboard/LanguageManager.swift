import Foundation

/// Manages translation target language preferences
/// Reads from shared App Group UserDefaults so settings sync between main app and extension
final class LanguageManager {

    static let shared = LanguageManager()

    private let settings = SharedSettings.shared

    // MARK: - Enabled Languages

    /// Currently enabled target languages for translation
    var enabledLanguages: Set<SupportedLanguage> {
        get { settings.enabledLanguages }
        set { settings.enabledLanguages = newValue }
    }

    /// Ordered list of enabled languages for consistent UI display
    var orderedEnabledLanguages: [SupportedLanguage] {
        let enabled = enabledLanguages
        // Maintain a stable display order: English, Japanese, Chinese, Spanish
        return SupportedLanguage.allCases.filter { enabled.contains($0) }
    }

    // MARK: - Toggle

    /// Toggle a language on or off. Ensures at least one language remains enabled.
    func toggle(_ language: SupportedLanguage) {
        var current = enabledLanguages
        if current.contains(language) {
            // Don't allow disabling the last language
            guard current.count > 1 else { return }
            current.remove(language)
        } else {
            current.insert(language)
        }
        enabledLanguages = current
    }

    /// Check if a specific language is enabled
    func isEnabled(_ language: SupportedLanguage) -> Bool {
        enabledLanguages.contains(language)
    }
}
