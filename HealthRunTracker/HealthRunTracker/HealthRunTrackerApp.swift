import SwiftUI

@main
struct HealthRunTrackerApp: App {
    @StateObject var healthManager = HealthManager()

    var body: some Scene {
        WindowGroup {
            MainView()
                .environmentObject(healthManager)
        }
    }
}
