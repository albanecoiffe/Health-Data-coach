import Foundation

struct ChatRequest: Codable {
    let message: String
    let snapshot: WeeklySnapshot
}
