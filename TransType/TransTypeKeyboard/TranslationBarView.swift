import UIKit

/// Delegate protocol for handling translation bar interactions
protocol TranslationBarViewDelegate: AnyObject {
    /// Called when user taps a translation result
    func translationBar(_ bar: TranslationBarView, didSelect result: TranslationResult)
    /// Called when user taps the settings button
    func translationBarDidTapSettings(_ bar: TranslationBarView)
}

/// Custom view that displays translation suggestions above the keyboard
/// Layout: [🇺🇸 Hello | 🇯🇵 こんにちは | ⚙️]
final class TranslationBarView: UIView {

    // MARK: - Constants

    /// Adaptive bar height: taller on iPad for better tap targets
    static var barHeight: CGFloat {
        UIDevice.current.userInterfaceIdiom == .pad ? 50 : 44
    }

    private static var isIPad: Bool {
        UIDevice.current.userInterfaceIdiom == .pad
    }

    private enum Layout {
        static let buttonCornerRadius: CGFloat = 8
        static let buttonHorizontalPadding: CGFloat = isIPad ? 20 : 12
        static let buttonVerticalPadding: CGFloat = isIPad ? 8 : 6
        static let flagTextSpacing: CGFloat = isIPad ? 6 : 4
        static let separatorWidth: CGFloat = 0.5
        static let translationFontSize: CGFloat = isIPad ? 16 : 14
        static let labelFontSize: CGFloat = isIPad ? 14 : 12
        static let settingsButtonWidth: CGFloat = isIPad ? 50 : 44
        static let bottomSeparatorHeight: CGFloat = 0.5

        private static var isIPad: Bool {
            UIDevice.current.userInterfaceIdiom == .pad
        }
    }

    // MARK: - Properties

    weak var delegate: TranslationBarViewDelegate?

    private var translationButtons: [TranslationButton] = []
    private let stackView = UIStackView()
    private let settingsButton = UIButton(type: .system)
    private let bottomSeparator = UIView()
    private let loadingLabel = UILabel()
    private let placeholderLabel = UILabel()
    private var currentResults: [TranslationResult] = []

    // MARK: - State

    enum BarState {
        case idle
        case loading
        case results([TranslationResult])
        case hidden
    }

    private(set) var barState: BarState = .idle

    // MARK: - Init

    override init(frame: CGRect) {
        super.init(frame: frame)
        setupUI()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupUI()
    }

    // MARK: - Setup

    private func setupUI() {
        // Background
        updateBackgroundColor()

        // Stack view for translation buttons
        stackView.axis = .horizontal
        stackView.distribution = .fillProportionally
        stackView.alignment = .center
        stackView.spacing = 0
        stackView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stackView)

        // Settings button
        settingsButton.setTitle("⚙️", for: .normal)
        settingsButton.titleLabel?.font = .systemFont(ofSize: 18)
        settingsButton.translatesAutoresizingMaskIntoConstraints = false
        settingsButton.addTarget(self, action: #selector(settingsButtonTapped), for: .touchUpInside)
        addSubview(settingsButton)

        // Bottom separator line
        bottomSeparator.backgroundColor = .separator
        bottomSeparator.translatesAutoresizingMaskIntoConstraints = false
        addSubview(bottomSeparator)

        // Loading label
        loadingLabel.text = "번역 중..."
        loadingLabel.font = .systemFont(ofSize: Layout.translationFontSize)
        loadingLabel.textColor = .secondaryLabel
        loadingLabel.textAlignment = .center
        loadingLabel.translatesAutoresizingMaskIntoConstraints = false
        loadingLabel.isHidden = true
        addSubview(loadingLabel)

        // Placeholder label
        placeholderLabel.text = "번역할 텍스트를 입력하세요"
        placeholderLabel.font = .systemFont(ofSize: Layout.translationFontSize)
        placeholderLabel.textColor = .tertiaryLabel
        placeholderLabel.textAlignment = .center
        placeholderLabel.translatesAutoresizingMaskIntoConstraints = false
        placeholderLabel.isHidden = true
        addSubview(placeholderLabel)

        // Constraints
        NSLayoutConstraint.activate([
            // Stack view
            stackView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 4),
            stackView.trailingAnchor.constraint(equalTo: settingsButton.leadingAnchor, constant: -4),
            stackView.topAnchor.constraint(equalTo: topAnchor),
            stackView.bottomAnchor.constraint(equalTo: bottomSeparator.topAnchor),

            // Settings button
            settingsButton.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -4),
            settingsButton.centerYAnchor.constraint(equalTo: stackView.centerYAnchor),
            settingsButton.widthAnchor.constraint(equalToConstant: Layout.settingsButtonWidth),
            settingsButton.heightAnchor.constraint(equalToConstant: Layout.settingsButtonWidth),

            // Bottom separator
            bottomSeparator.leadingAnchor.constraint(equalTo: leadingAnchor),
            bottomSeparator.trailingAnchor.constraint(equalTo: trailingAnchor),
            bottomSeparator.bottomAnchor.constraint(equalTo: bottomAnchor),
            bottomSeparator.heightAnchor.constraint(equalToConstant: Layout.bottomSeparatorHeight),

            // Loading label
            loadingLabel.centerXAnchor.constraint(equalTo: stackView.centerXAnchor),
            loadingLabel.centerYAnchor.constraint(equalTo: stackView.centerYAnchor),

            // Placeholder label
            placeholderLabel.centerXAnchor.constraint(equalTo: stackView.centerXAnchor),
            placeholderLabel.centerYAnchor.constraint(equalTo: stackView.centerYAnchor),
        ])

        setState(.idle)
    }

    // MARK: - State Management

    func setState(_ state: BarState) {
        barState = state

        switch state {
        case .idle:
            showIdle()
        case .loading:
            showLoading()
        case .results(let results):
            showResults(results)
        case .hidden:
            hideBar()
        }
    }

    private func showIdle() {
        clearTranslationButtons()
        loadingLabel.isHidden = true
        placeholderLabel.isHidden = false
        animateAppear()
    }

    private func showLoading() {
        clearTranslationButtons()
        loadingLabel.isHidden = false
        placeholderLabel.isHidden = true
        startLoadingAnimation()
    }

    private func showResults(_ results: [TranslationResult]) {
        loadingLabel.isHidden = true
        placeholderLabel.isHidden = true
        stopLoadingAnimation()

        guard !results.isEmpty else {
            setState(.idle)
            return
        }

        currentResults = results
        clearTranslationButtons()
        buildTranslationButtons(for: results)

        // Fade-in animation for results
        for button in translationButtons {
            button.alpha = 0
        }

        UIView.animate(withDuration: 0.2) {
            for button in self.translationButtons {
                button.alpha = 1
            }
        }
    }

    private func hideBar() {
        UIView.animate(withDuration: 0.15, animations: {
            self.transform = CGAffineTransform(translationX: 0, y: -Self.barHeight)
            self.alpha = 0
        }) { _ in
            self.isHidden = true
            self.transform = .identity
        }
    }

    func showBar() {
        guard isHidden else { return }
        isHidden = false
        alpha = 0
        animateAppear()
    }

    private func animateAppear() {
        guard !isHidden else { return }
        UIView.animate(withDuration: 0.15) {
            self.alpha = 1
        }
    }

    // MARK: - Loading Animation

    private var loadingTimer: Timer?

    private func startLoadingAnimation() {
        var dotCount = 0
        loadingTimer?.invalidate()
        loadingTimer = Timer.scheduledTimer(withTimeInterval: 0.3, repeats: true) { [weak self] _ in
            dotCount = (dotCount + 1) % 4
            let dots = String(repeating: ".", count: dotCount)
            self?.loadingLabel.text = "번역 중\(dots)"
        }
    }

    private func stopLoadingAnimation() {
        loadingTimer?.invalidate()
        loadingTimer = nil
    }

    // MARK: - Button Management

    private func clearTranslationButtons() {
        translationButtons.forEach { $0.removeFromSuperview() }
        translationButtons.removeAll()

        // Also remove separators
        stackView.arrangedSubviews.forEach { $0.removeFromSuperview() }
    }

    private func buildTranslationButtons(for results: [TranslationResult]) {
        for (index, result) in results.enumerated() {
            let button = TranslationButton(result: result)
            button.onTap = { [weak self] in
                guard let self = self else { return }
                self.delegate?.translationBar(self, didSelect: result)
            }
            stackView.addArrangedSubview(button)
            translationButtons.append(button)

            // Add separator between buttons
            if index < results.count - 1 {
                let separator = createVerticalSeparator()
                stackView.addArrangedSubview(separator)
            }
        }
    }

    private func createVerticalSeparator() -> UIView {
        let separator = UIView()
        separator.backgroundColor = .separator
        separator.translatesAutoresizingMaskIntoConstraints = false
        separator.widthAnchor.constraint(equalToConstant: Layout.separatorWidth).isActive = true
        separator.heightAnchor.constraint(equalToConstant: 24).isActive = true
        return separator
    }

    // MARK: - Dark/Light Mode

    override func traitCollectionDidChange(_ previousTraitCollection: UITraitCollection?) {
        super.traitCollectionDidChange(previousTraitCollection)
        if traitCollection.hasDifferentColorAppearance(comparedTo: previousTraitCollection) {
            updateBackgroundColor()
        }
    }

    private func updateBackgroundColor() {
        if traitCollection.userInterfaceStyle == .dark {
            backgroundColor = .systemGray5
        } else {
            backgroundColor = .systemGray6
        }
    }

    // MARK: - Actions

    @objc private func settingsButtonTapped() {
        delegate?.translationBarDidTapSettings(self)
    }

    // MARK: - Cleanup

    deinit {
        loadingTimer?.invalidate()
    }
}

// MARK: - TranslationButton

/// Individual tappable button displaying a translation result with flag emoji
private final class TranslationButton: UIView {

    var onTap: (() -> Void)?

    private let flagLabel = UILabel()
    private let textLabel = UILabel()
    private let highlightView = UIView()
    private let containerStack = UIStackView()

    init(result: TranslationResult) {
        super.init(frame: .zero)
        setupUI(with: result)
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    private func setupUI(with result: TranslationResult) {
        // Highlight background (hidden by default)
        highlightView.backgroundColor = UIColor.systemBlue.withAlphaComponent(0.15)
        highlightView.layer.cornerRadius = 8
        highlightView.alpha = 0
        highlightView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(highlightView)

        let isIPad = UIDevice.current.userInterfaceIdiom == .pad

        // Flag label
        flagLabel.text = result.language.flagEmoji
        flagLabel.font = .systemFont(ofSize: isIPad ? 20 : 16)
        flagLabel.setContentHuggingPriority(.required, for: .horizontal)

        // Translation text label
        textLabel.text = result.translatedText
        textLabel.font = .systemFont(ofSize: isIPad ? 16 : 14, weight: .medium)
        textLabel.textColor = .label
        textLabel.lineBreakMode = .byTruncatingTail

        // Container stack
        containerStack.axis = .horizontal
        containerStack.spacing = isIPad ? 6 : 4
        containerStack.alignment = .center
        containerStack.translatesAutoresizingMaskIntoConstraints = false
        containerStack.addArrangedSubview(flagLabel)
        containerStack.addArrangedSubview(textLabel)
        containerStack.isUserInteractionEnabled = false
        addSubview(containerStack)

        NSLayoutConstraint.activate([
            highlightView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 2),
            highlightView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -2),
            highlightView.topAnchor.constraint(equalTo: topAnchor, constant: 4),
            highlightView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -4),

            containerStack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 12),
            containerStack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -12),
            containerStack.centerYAnchor.constraint(equalTo: centerYAnchor),
        ])

        // Tap gesture
        let tap = UITapGestureRecognizer(target: self, action: #selector(handleTap))
        addGestureRecognizer(tap)
        isUserInteractionEnabled = true
    }

    @objc private func handleTap() {
        // Tap animation: scale down then back, with highlight
        UIView.animate(withDuration: 0.1, animations: {
            self.transform = CGAffineTransform(scaleX: 0.95, y: 0.95)
            self.highlightView.alpha = 1
        }) { _ in
            UIView.animate(withDuration: 0.1) {
                self.transform = .identity
                self.highlightView.alpha = 0
            }
        }

        onTap?()
    }
}
