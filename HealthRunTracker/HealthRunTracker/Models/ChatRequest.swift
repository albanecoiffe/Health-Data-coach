import Foundation

struct ChatRequest: Codable {
    let message: String
    let snapshot: WeeklySnapshot

    // Pour COMPARE_PERIODS (batch)
    let snapshots: [String: WeeklySnapshot]?
    let meta: [String: String]?

    init(message: String,
         snapshot: WeeklySnapshot,
         snapshots: [String: WeeklySnapshot]? = nil,
         meta: [String: String]? = nil) {
        self.message = message
        self.snapshot = snapshot
        self.snapshots = snapshots
        self.meta = meta
    }
}


