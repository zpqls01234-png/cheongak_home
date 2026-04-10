import UIKit

/// Main keyboard extension view controller
/// Adds a translation suggestion bar above the system keyboard.
/// When the user types Korean, it displays English/Japanese translations
/// in the bar. Tapping a translation replaces the Korean input.
class KeyboardViewController: UIInputViewController {

    // MARK: - Properties

    /// Translation suggestion bar displayed above the keyboard
    private var translationBar: TranslationBarView!

    /// Service that handles debounced translation
    private let translationService = TranslationService()

    /// Tracks the current Korean text being translated
    private var currentInputText: String = ""

    /// Haptic feedback generator (pre-warmed for responsiveness)
    private let hapticGenerator = UIImpactFeedbackGenerator(style: .light)

    /// Height constraint for the translation bar container
    private var barHeightConstraint: NSLayoutConstraint?

    /// Next keyboard button for iPad (globe icon)
    private var nextKeyboardButton: UIButton?

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        setupTranslationBar()
        setupNextKeyboardButton()
        setupTranslationService()
        hapticGenerator.prepare()
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        // Refresh settings every time the keyboard appears
        translationService.cancel()
        translationBar.setState(.idle)
        translationBar.showBar()
    }

    override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)
        translationService.cancel()
    }

    override func viewWillTransition(
        to size: CGSize,
        with coordinator: UIViewControllerTransitionCoordinator
    ) {
        super.viewWillTransition(to: size, with: coordinator)
        // Update bar height on rotation (iPad landscape/portrait)
        coordinator.animate(alongsideTransition: { _ in
            self.barHeightConstraint?.constant = TranslationBarView.barHeight
        })
    }

    // MARK: - Setup

    private func setupTranslationBar() {
        // Create translation bar
        translationBar = TranslationBarView()
        translationBar.delegate = self
        translationBar.translatesAutoresizingMaskIntoConstraints = false

        // Create a container that serves as the inputView's accessory
        // The bar sits at the top of our input view
        let barContainer = UIView()
        barContainer.translatesAutoresizingMaskIntoConstraints = false
        barContainer.addSubview(translationBar)

        // Add to the keyboard's input view
        view.addSubview(barContainer)

        // Constraints: bar at the top of the keyboard extension view
        barHeightConstraint = barContainer.heightAnchor.constraint(
            equalToConstant: TranslationBarView.barHeight
        )

        NSLayoutConstraint.activate([
            barContainer.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            barContainer.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            barContainer.topAnchor.constraint(equalTo: view.topAnchor),
            barHeightConstraint!,

            translationBar.leadingAnchor.constraint(equalTo: barContainer.leadingAnchor),
            translationBar.trailingAnchor.constraint(equalTo: barContainer.trailingAnchor),
            translationBar.topAnchor.constraint(equalTo: barContainer.topAnchor),
            translationBar.bottomAnchor.constraint(equalTo: barContainer.bottomAnchor),
        ])
    }

    /// Add a globe/next-keyboard button so users can switch keyboards.
    /// This is especially important on iPad where the system may not
    /// show the globe key automatically for custom keyboards.
    private func setupNextKeyboardButton() {
        guard needsInputModeSwitchKey else { return }

        let button = UIButton(type: .system)
        button.setImage(
            UIImage(systemName: "globe"),
            for: .normal
        )
        button.tintColor = .label
        button.translatesAutoresizingMaskIntoConstraints = false
        button.sizeToFit()

        // Wire the system-provided action for switching keyboards
        button.addTarget(
            self,
            action: #selector(handleInputModeList(from:with:)),
            for: .allTouchEvents
        )

        view.addSubview(button)
        NSLayoutConstraint.activate([
            button.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 8),
            button.bottomAnchor.constraint(equalTo: view.bottomAnchor, constant: -4),
            button.widthAnchor.constraint(equalToConstant: 32),
            button.heightAnchor.constraint(equalToConstant: 32),
        ])
        nextKeyboardButton = button
    }

    private func setupTranslationService() {
        translationService.onTranslationStarted = { [weak self] in
            self?.translationBar.setState(.loading)
        }

        translationService.onTranslationsReady = { [weak self] results in
            guard let self = self else { return }
            if results.isEmpty {
                self.translationBar.setState(.idle)
            } else {
                self.translationBar.setState(.results(results))
            }
        }
    }

    // MARK: - Text Input Monitoring

    override func textDidChange(_ textInput: UITextInput?) {
        super.textDidChange(textInput)

        guard SharedSettings.shared.autoTranslateEnabled else {
            translationBar.setState(.hidden)
            return
        }

        // Get text before cursor from the document proxy
        let beforeInput = textDocumentProxy.documentContextBeforeInput ?? ""

        // Extract the last word (text after the last space)
        let lastWord = TranslationService.extractLastWord(from: beforeInput)

        guard !lastWord.isEmpty else {
            currentInputText = ""
            translationBar.setState(.idle)
            translationService.cancel()
            return
        }

        // Only translate Korean text
        if TranslationService.isKorean(lastWord) {
            currentInputText = lastWord
            translationService.translate(text: lastWord)
        } else {
            // Non-Korean text: hide translation bar
            currentInputText = ""
            translationBar.setState(.idle)
            translationService.cancel()
        }
    }

    // MARK: - Translation Selection

    /// Replace the current Korean input with the selected translation
    private func applyTranslation(_ translatedText: String) {
        // 1. Delete the original Korean text character by character
        //    We need to count the actual characters that the proxy will delete
        let deleteCount = currentInputText.count
        for _ in 0..<deleteCount {
            textDocumentProxy.deleteBackward()
        }

        // 2. Insert the translated text
        textDocumentProxy.insertText(translatedText)

        // 3. Add trailing space
        textDocumentProxy.insertText(" ")

        // 4. Haptic feedback
        if SharedSettings.shared.hapticFeedbackEnabled {
            hapticGenerator.impactOccurred()
            hapticGenerator.prepare()
        }

        // 5. Reset state
        currentInputText = ""
        translationBar.setState(.idle)
        translationService.cancel()
    }

    // MARK: - Next Keyboard

    override func textWillChange(_ textInput: UITextInput?) {
        super.textWillChange(textInput)
    }
}

// MARK: - TranslationBarViewDelegate

extension KeyboardViewController: TranslationBarViewDelegate {

    func translationBar(_ bar: TranslationBarView, didSelect result: TranslationResult) {
        applyTranslation(result.translatedText)
    }

    func translationBarDidTapSettings(_ bar: TranslationBarView) {
        // In a keyboard extension, we can't open the main app directly.
        // Instead, cycle through enabled language configurations.
        // A more complete implementation could use a popover or
        // open the main app via URL scheme.
        cycleLanguageConfiguration()
    }

    /// Quick toggle: cycle through language presets from the keyboard
    private func cycleLanguageConfiguration() {
        let manager = LanguageManager.shared
        let current = manager.enabledLanguages

        // Cycle: Both → English only → Japanese only → Both
        if current.contains(.english) && current.contains(.japanese) {
            manager.enabledLanguages = [.english]
        } else if current.contains(.english) {
            manager.enabledLanguages = [.japanese]
        } else {
            manager.enabledLanguages = [.english, .japanese]
        }

        // Re-trigger translation with new language set if we have text
        if !currentInputText.isEmpty {
            translationService.translate(text: currentInputText)
        } else {
            translationBar.setState(.idle)
        }

        // Brief haptic to confirm setting change
        if SharedSettings.shared.hapticFeedbackEnabled {
            let generator = UINotificationFeedbackGenerator()
            generator.notificationOccurred(.success)
        }
    }
}
