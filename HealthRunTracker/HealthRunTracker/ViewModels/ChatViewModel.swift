import Foundation
import Combine

struct CoachResponse: Codable {
    let reply: String
}
struct CoachAPIResponse: Codable {
    let reply: String?
    let type: String?
    let period: PeriodPayload?
}

struct PeriodPayload: Codable {
    let start: String
    let end: String
}


class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var currentInput: String = ""

    private let healthManager: HealthManager

    init(healthManager: HealthManager) {
        self.healthManager = healthManager
    }

    func sendMessage() {
        let text = currentInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }

        let userMsg = ChatMessage(text: text, isUser: true)
        messages.append(userMsg)
        currentInput = ""

        // 🔑 On autorise toujours l'envoi
        Task {
            let reply = await askPythonBot(text) ?? "Erreur dans la réponse du coach."
            await MainActor.run {
                self.messages.append(ChatMessage(text: reply, isUser: false))
            }
        }
    }


    func askPythonBot(_ message: String) async -> String? {
        //NSLog("🔥 askPythonBot called with message: %@", message)


        guard let url = URL(string: "http://192.168.1.77:8000/chat") else {
            return "URL invalide."
        }

        // Snapshot par défaut
        let snapshot = healthManager.makeWeeklySnapshot()

        let payload = ChatRequest(
            message: message,
            snapshot: snapshot
        )

        var req = URLRequest(url: url)
        req.httpMethod = "POST"   // ✅ CRUCIAL
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.timeoutInterval = 30

        do {
            let encoder = JSONEncoder()
            encoder.keyEncodingStrategy = .convertToSnakeCase
            req.httpBody = try encoder.encode(payload)
        } catch {
            return "Erreur encodage JSON"
        }

        do {
            let (data, response) = try await URLSession.shared.data(for: req)

            guard let http = response as? HTTPURLResponse,
                  (200...299).contains(http.statusCode) else {
                return "Erreur serveur"
            }

            let decoded = try JSONDecoder().decode(CoachAPIResponse.self, from: data)
            //NSLog("🟣 RAW RESPONSE: %@", String(data: data, encoding: .utf8) ?? "nil")
            //NSLog("🟣 DECODED TYPE: %@", decoded.type ?? "nil")
            //NSLog(
                //"🟣 DECODED PERIOD: %@ → %@",
               // decoded.period?.start ?? "nil",
               // decoded.period?.end ?? "nil"
            //)

            
            // 🟢 Réponse normale
            if let reply = decoded.reply {
                return reply
            }

            // 🟠 Demande d’un autre snapshot
            if decoded.type == "REQUEST_SNAPSHOT",
               let period = decoded.period {

                let formatter = DateFormatter()
                formatter.dateFormat = "yyyy-MM-dd"

                guard
                    let start = formatter.date(from: period.start),
                    let end = formatter.date(from: period.end)
                else {
                    return "Erreur période"
                }

                return await requestSnapshotAndRetry(
                    message: message,
                    start: start,
                    end: end
                )
            }

            return "Réponse invalide du serveur"

        } catch {
            print("❌ ERREUR RÉSEAU:", error)
            return "Le coach ne répond pas actuellement"
        }
    }


    private func sendPayload(_ payload: ChatRequest) async -> String? {

        guard let url = URL(string: "http://192.168.1.77:8000/chat") else {
            return "URL invalide."
        }

        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            encoder.keyEncodingStrategy = .convertToSnakeCase
            req.httpBody = try encoder.encode(payload)

            let (data, _) = try await URLSession.shared.data(for: req)
            let decoded = try JSONDecoder().decode(CoachAPIResponse.self, from: data)

            return decoded.reply

        } catch {
            return "Erreur serveur."
        }
    }

    
    func requestSnapshotAndRetry(
        message: String,
        start: Date,
        end: Date
    ) async -> String? {

        await withCheckedContinuation { continuation in

            healthManager.makeSnapshot(from: start, to: end) { snapshot in
                Task {
                    let payload = ChatRequest(
                        message: message,
                        snapshot: snapshot
                    )

                    let reply = await self.sendPayload(payload)
                    continuation.resume(returning: reply)
                }
            }
        }
    }


}
