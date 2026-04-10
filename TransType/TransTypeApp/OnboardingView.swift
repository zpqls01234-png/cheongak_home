import SwiftUI

/// Onboarding view that guides users through enabling the TransType keyboard
struct OnboardingView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var isKeyboardEnabled = false
    @State private var checkTimer: Timer?

    var body: some View {
        ScrollView {
            VStack(spacing: 32) {
                // Header
                headerSection

                // Status indicator
                statusSection

                // Steps
                stepsSection

                // Open Settings button
                openSettingsButton

                // Done button (if keyboard is active)
                if isKeyboardEnabled {
                    doneButton
                }
            }
            .padding(24)
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("키보드 설정")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            checkKeyboardStatus()
            // Periodically check if keyboard was enabled
            checkTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { _ in
                checkKeyboardStatus()
            }
        }
        .onDisappear {
            checkTimer?.invalidate()
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(spacing: 12) {
            Image(systemName: "keyboard.badge.ellipsis")
                .font(.system(size: 60))
                .foregroundStyle(.blue)

            Text("TransType 키보드 활성화")
                .font(.title2)
                .fontWeight(.bold)

            Text("아래 단계를 따라 키보드를 추가해주세요")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
    }

    // MARK: - Status

    private var statusSection: some View {
        HStack(spacing: 12) {
            Image(systemName: isKeyboardEnabled ? "checkmark.circle.fill" : "exclamationmark.circle")
                .font(.title3)
                .foregroundStyle(isKeyboardEnabled ? .green : .orange)

            Text(isKeyboardEnabled
                 ? "키보드가 활성화되었습니다"
                 : "키보드가 아직 활성화되지 않았습니다")
                .font(.subheadline)
                .fontWeight(.medium)
        }
        .frame(maxWidth: .infinity)
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(isKeyboardEnabled
                      ? Color.green.opacity(0.1)
                      : Color.orange.opacity(0.1))
        )
    }

    // MARK: - Steps

    private var stepsSection: some View {
        VStack(spacing: 0) {
            stepRow(
                number: 1,
                icon: "gear",
                title: "설정 앱 열기",
                description: "iPhone 설정 앱을 열어주세요"
            )

            Divider().padding(.leading, 56)

            stepRow(
                number: 2,
                icon: "text.justify.leading",
                title: "일반 → 키보드",
                description: "\"일반\" 메뉴에서 \"키보드\"를 선택하세요"
            )

            Divider().padding(.leading, 56)

            stepRow(
                number: 3,
                icon: "plus.rectangle.on.rectangle",
                title: "키보드 → 새로운 키보드 추가",
                description: "\"키보드\" 메뉴에서 \"새로운 키보드 추가...\"를 탭하세요"
            )

            Divider().padding(.leading, 56)

            stepRow(
                number: 4,
                icon: "magnifyingglass",
                title: "TransType 선택",
                description: "목록에서 \"TransType\"을 찾아 탭하세요"
            )

            Divider().padding(.leading, 56)

            stepRow(
                number: 5,
                icon: "lock.open",
                title: "전체 접근 허용",
                description: "TransType을 탭한 후 \"전체 접근 허용\" 토글을 켜주세요. 번역 기능을 위해 필요합니다."
            )
        }
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.secondarySystemGroupedBackground))
        )
    }

    private func stepRow(number: Int, icon: String, title: String, description: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            // Step number badge
            Text("\(number)")
                .font(.caption)
                .fontWeight(.bold)
                .foregroundStyle(.white)
                .frame(width: 24, height: 24)
                .background(Circle().fill(.blue))

            VStack(alignment: .leading, spacing: 4) {
                Label(title, systemImage: icon)
                    .font(.subheadline)
                    .fontWeight(.semibold)

                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            Spacer()
        }
        .padding(16)
    }

    // MARK: - Buttons

    private var openSettingsButton: some View {
        Button {
            if let url = URL(string: UIApplication.openSettingsURLString) {
                UIApplication.shared.open(url)
            }
        } label: {
            Label("설정 앱 열기", systemImage: "gear")
                .font(.headline)
                .frame(maxWidth: .infinity)
                .padding(14)
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .fill(.blue)
                )
                .foregroundStyle(.white)
        }
    }

    private var doneButton: some View {
        Button {
            dismiss()
        } label: {
            Text("완료")
                .font(.headline)
                .frame(maxWidth: .infinity)
                .padding(14)
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .fill(.green)
                )
                .foregroundStyle(.white)
        }
    }

    // MARK: - Keyboard Status Check

    private func checkKeyboardStatus() {
        // Check if TransType keyboard is enabled by inspecting
        // the list of active keyboard extensions
        let bundleID = "com.transtype.app.keyboard"
        if let keyboards = UserDefaults.standard.object(
            forKey: "AppleKeyboards"
        ) as? [String] {
            isKeyboardEnabled = keyboards.contains(bundleID)
        } else {
            // Fallback: check if our extension bundle is in the active list
            // This is a best-effort check since iOS doesn't provide a direct API
            isKeyboardEnabled = false
        }
    }
}

#Preview {
    NavigationStack {
        OnboardingView()
    }
}
