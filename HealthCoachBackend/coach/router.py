# Rôle : chef d’orchestre
# C’est le cerveau central : reçoit ChatRequest, analyse le message utilisateur, détecte l’intent, extrait la période
# décide : répondre directement ou demander un snapshot plus précis à l’app
# Aucun calcul HealthKit ici
# Il travaille uniquement sur le snapshot reçu


from coach.logic import generate_reply
from coach.time_parser import parse_time_query, resolve_time_query
from coach.intent_parser import detect_intent
from schemas import ChatRequest

from datetime import date


def handle_chat(req: ChatRequest):
    tq = parse_time_query(req.message)
    start, end = resolve_time_query(tq)

    # Pydantic parse period.start/end en date → parfait
    if req.snapshot.period.start != start or req.snapshot.period.end != end:
        return {
            "type": "REQUEST_SNAPSHOT",
            "period": {"start": start.isoformat(), "end": end.isoformat()},
        }

    intent = detect_intent(req.message)
    reply = generate_reply(intent, req.snapshot)
    return {"reply": reply}
