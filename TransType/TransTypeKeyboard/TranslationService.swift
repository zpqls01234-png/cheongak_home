import Foundation
import NaturalLanguage

/// Result of a translation request
struct TranslationResult {
    let sourceText: String
    let language: SupportedLanguage
    let translatedText: String
}

/// Handles translation logic with debouncing and multiple backend support
final class TranslationService {

    // MARK: - Properties

    private var debounceTimer: Timer?
    private var debounceInterval: Double {
        SharedSettings.shared.debounceInterval
    }

    /// Callback invoked on the main thread when translations are ready
    var onTranslationsReady: (([TranslationResult]) -> Void)?

    /// Callback invoked when translation starts (for loading indicator)
    var onTranslationStarted: (() -> Void)?

    // MARK: - Offline Dictionary (MVP Fallback)

    /// Basic Korean → English dictionary for offline/fallback use
    private let koreanToEnglishDict: [String: String] = [
        "안녕하세요": "Hello",
        "안녕": "Hi",
        "감사합니다": "Thank you",
        "감사": "Thanks",
        "사랑": "Love",
        "좋아": "Good",
        "좋아요": "Good",
        "네": "Yes",
        "아니오": "No",
        "아니": "No",
        "물": "Water",
        "밥": "Rice",
        "집": "House",
        "학교": "School",
        "선생님": "Teacher",
        "학생": "Student",
        "친구": "Friend",
        "가족": "Family",
        "엄마": "Mom",
        "아빠": "Dad",
        "오빠": "Brother",
        "언니": "Sister",
        "동생": "Sibling",
        "이름": "Name",
        "나이": "Age",
        "오늘": "Today",
        "내일": "Tomorrow",
        "어제": "Yesterday",
        "시간": "Time",
        "날씨": "Weather",
        "사람": "Person",
        "여행": "Travel",
        "음식": "Food",
        "커피": "Coffee",
        "회사": "Company",
        "일": "Work",
        "공부": "Study",
        "운동": "Exercise",
        "영화": "Movie",
        "음악": "Music",
        "책": "Book",
        "컴퓨터": "Computer",
        "전화": "Phone",
        "인터넷": "Internet",
        "세계": "World",
        "한국": "Korea",
        "미국": "America",
        "일본": "Japan",
        "중국": "China",
        "행복": "Happiness",
        "건강": "Health",
        "문제": "Problem",
        "질문": "Question",
        "대답": "Answer",
        "의미": "Meaning",
        "생각": "Thought",
        "마음": "Heart",
        "기분": "Feeling",
        "꿈": "Dream",
        "희망": "Hope",
        "미래": "Future",
        "과거": "Past",
        "현재": "Present",
        "시작": "Start",
        "끝": "End",
        "가게": "Store",
        "병원": "Hospital",
        "은행": "Bank",
        "공원": "Park",
        "역": "Station",
        "길": "Road",
        "차": "Car",
        "버스": "Bus",
        "지하철": "Subway",
        "비행기": "Airplane",
        "고맙습니다": "Thank you",
        "미안합니다": "Sorry",
        "미안": "Sorry",
        "괜찮아": "It's okay",
        "좋은": "Good",
        "나쁜": "Bad",
        "큰": "Big",
        "작은": "Small",
        "새로운": "New",
        "오래된": "Old",
        "빠른": "Fast",
        "느린": "Slow",
        "뜨거운": "Hot",
        "차가운": "Cold",
        "예쁜": "Pretty",
        "맛있는": "Delicious",
        "재미있는": "Fun",
        "중요한": "Important",
    ]

    /// Basic Korean → Japanese dictionary for offline/fallback use
    private let koreanToJapaneseDict: [String: String] = [
        "안녕하세요": "こんにちは",
        "안녕": "こんにちは",
        "감사합니다": "ありがとうございます",
        "감사": "感謝",
        "사랑": "愛",
        "좋아": "いいね",
        "좋아요": "いいですね",
        "네": "はい",
        "아니오": "いいえ",
        "아니": "いいえ",
        "물": "水",
        "밥": "ご飯",
        "집": "家",
        "학교": "学校",
        "선생님": "先生",
        "학생": "学生",
        "친구": "友達",
        "가족": "家族",
        "엄마": "お母さん",
        "아빠": "お父さん",
        "오빠": "お兄さん",
        "언니": "お姉さん",
        "동생": "弟妹",
        "이름": "名前",
        "나이": "年齢",
        "오늘": "今日",
        "내일": "明日",
        "어제": "昨日",
        "시간": "時間",
        "날씨": "天気",
        "사람": "人",
        "여행": "旅行",
        "음식": "食べ物",
        "커피": "コーヒー",
        "회사": "会社",
        "일": "仕事",
        "공부": "勉強",
        "운동": "運動",
        "영화": "映画",
        "음악": "音楽",
        "책": "本",
        "컴퓨터": "コンピュータ",
        "전화": "電話",
        "인터넷": "インターネット",
        "세계": "世界",
        "한국": "韓国",
        "미국": "アメリカ",
        "일본": "日本",
        "중국": "中国",
        "행복": "幸せ",
        "건강": "健康",
        "문제": "問題",
        "질문": "質問",
        "대답": "答え",
        "의미": "意味",
        "생각": "考え",
        "마음": "心",
        "기분": "気分",
        "꿈": "夢",
        "희망": "希望",
        "미래": "未来",
        "과거": "過去",
        "현재": "現在",
        "시작": "始まり",
        "끝": "終わり",
        "가게": "店",
        "병원": "病院",
        "은행": "銀行",
        "공원": "公園",
        "역": "駅",
        "길": "道",
        "차": "車",
        "버스": "バス",
        "지하철": "地下鉄",
        "비행기": "飛行機",
        "고맙습니다": "ありがとうございます",
        "미안합니다": "すみません",
        "미안": "ごめん",
        "괜찮아": "大丈夫",
        "좋은": "良い",
        "나쁜": "悪い",
        "큰": "大きい",
        "작은": "小さい",
        "새로운": "新しい",
        "오래된": "古い",
        "빠른": "速い",
        "느린": "遅い",
        "뜨거운": "熱い",
        "차가운": "冷たい",
        "예쁜": "綺麗",
        "맛있는": "美味しい",
        "재미있는": "面白い",
        "중요한": "重要",
    ]

    // MARK: - Public API

    /// Translate the given Korean text with debounce
    func translate(text: String) {
        debounceTimer?.invalidate()
        onTranslationStarted?()

        debounceTimer = Timer.scheduledTimer(
            withTimeInterval: debounceInterval,
            repeats: false
        ) { [weak self] _ in
            self?.performTranslation(text: text)
        }
    }

    /// Cancel any pending translation
    func cancel() {
        debounceTimer?.invalidate()
        debounceTimer = nil
    }

    // MARK: - Translation Backends

    private func performTranslation(text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            DispatchQueue.main.async { [weak self] in
                self?.onTranslationsReady?([])
            }
            return
        }

        let enabledLanguages = SharedSettings.shared.enabledLanguages

        // Use offline dictionary as the reliable MVP backend.
        // Apple Translation Framework (iOS 17.4+) can be integrated
        // when running on a compatible device with the framework available.
        var results: [TranslationResult] = []

        if enabledLanguages.contains(.english) {
            let translated = offlineTranslate(text: trimmed, to: .english)
            if let translated = translated {
                results.append(TranslationResult(
                    sourceText: trimmed,
                    language: .english,
                    translatedText: translated
                ))
            }
        }

        if enabledLanguages.contains(.japanese) {
            let translated = offlineTranslate(text: trimmed, to: .japanese)
            if let translated = translated {
                results.append(TranslationResult(
                    sourceText: trimmed,
                    language: .japanese,
                    translatedText: translated
                ))
            }
        }

        // Additional languages
        for lang in enabledLanguages where lang != .english && lang != .japanese {
            let translated = offlineTranslate(text: trimmed, to: lang)
            if let translated = translated {
                results.append(TranslationResult(
                    sourceText: trimmed,
                    language: lang,
                    translatedText: translated
                ))
            }
        }

        DispatchQueue.main.async { [weak self] in
            self?.onTranslationsReady?(results)
        }
    }

    /// Offline dictionary-based translation (MVP fallback)
    private func offlineTranslate(text: String, to language: SupportedLanguage) -> String? {
        let dict: [String: String]
        switch language {
        case .english:
            dict = koreanToEnglishDict
        case .japanese:
            dict = koreanToJapaneseDict
        default:
            // Unsupported language for offline translation
            return nil
        }

        // Exact match first
        if let result = dict[text] {
            return result
        }

        // Try partial match: check if input is a prefix of any dictionary key
        // This helps with incomplete word input (e.g., "안녕하" → "안녕하세요" → "Hello")
        let partialMatches = dict.filter { $0.key.hasPrefix(text) }
        if let bestMatch = partialMatches.min(by: { $0.key.count < $1.key.count }) {
            return bestMatch.value
        }

        // Try if any dictionary key is a prefix of the input
        let reverseMatches = dict.filter { text.hasPrefix($0.key) }
        if let bestMatch = reverseMatches.max(by: { $0.key.count < $1.key.count }) {
            return bestMatch.value
        }

        return nil
    }

    // MARK: - Korean Detection

    /// Check if the given text contains Korean characters
    static func isKorean(_ text: String) -> Bool {
        guard !text.isEmpty else { return false }
        for scalar in text.unicodeScalars {
            // Hangul Syllables (가-힣)
            if scalar.value >= 0xAC00 && scalar.value <= 0xD7A3 { return true }
            // Hangul Jamo (ㄱ-ㅎ)
            if scalar.value >= 0x3131 && scalar.value <= 0x314E { return true }
            // Hangul Jamo (ㅏ-ㅣ)
            if scalar.value >= 0x314F && scalar.value <= 0x3163 { return true }
            // Hangul Compatibility Jamo
            if scalar.value >= 0x1100 && scalar.value <= 0x11FF { return true }
        }
        return false
    }

    /// Extract the last word (after the last space) from text
    static func extractLastWord(from text: String) -> String {
        let trimmed = text.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return "" }
        let components = trimmed.components(separatedBy: .whitespaces)
        return components.last ?? ""
    }
}
