import SwiftUI

@main
struct TransTypeApp: App {
    @AppStorage(
        UserDefaultsKeys.autoTranslateEnabled,
        store: UserDefaults(suiteName: appGroupSuiteName)
    )
    private var hasCompletedOnboarding: Bool = false

    var body: some Scene {
        WindowGroup {
            NavigationStack {
                ContentView()
            }
        }
    }
}
