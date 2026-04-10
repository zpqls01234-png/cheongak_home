import Foundation

/// Supported translation target languages
enum SupportedLanguage: String, CaseIterable, Codable, Identifiable {
    case english = "en"
    case japanese = "ja"
    case chinese = "zh"
    case spanish = "es"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .english:  return "English"
        case .japanese: return "日本語"
        case .chinese:  return "中文"
        case .spanish:  return "Español"
        }
    }

    var flagEmoji: String {
        switch self {
        case .english:  return "🇺🇸"
        case .japanese: return "🇯🇵"
        case .chinese:  return "🇨🇳"
        case .spanish:  return "🇪🇸"
        }
    }

    var localizedLabel: String {
        switch self {
        case .english:  return "영어"
        case .japanese: return "일본어"
        case .chinese:  return "중국어"
        case .spanish:  return "스페인어"
        }
    }

    /// Default enabled languages
    static var defaultEnabled: Set<SupportedLanguage> {
        [.english, .japanese]
    }
}
