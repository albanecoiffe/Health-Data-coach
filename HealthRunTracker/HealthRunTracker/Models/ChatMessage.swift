//
//  ChatMessage.swift
//  HealthRunTracker
//
//  Created by Albane Coiffe on 10/12/2025.
//

import Foundation

struct ChatMessage: Identifiable, Equatable {
    let id = UUID()
    let text: String
    let isUser: Bool
}
