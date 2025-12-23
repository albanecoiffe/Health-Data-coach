# Rôle : génération de texte
# Il transforme : {"distance": 129.2,"sessions": 14,"duration": 804}
# en : "Sur cette période, tu as couru 129.2 km en 14 séances..."
# Plus tard : templates, variantes
# LLM local si tu veux


from models import WeeklySnapshot
from coach.intent_parser import Intent


def make_reply(intent: Intent, snapshot: WeeklySnapshot) -> str:
    t = snapshot.totals

    if t.sessions == 0:
        return "Sur cette période, tu n’as enregistré aucune séance."

    if intent == Intent.SUMMARY:
        return (
            f"Sur cette période, tu as couru "
            f"{t.distance_km:.1f} km en {t.sessions} séances, "
            f"pour un total de {int(t.duration_min)} minutes."
        )

    if intent == Intent.STATS:
        return f"Tu as parcouru {t.distance_km:.1f} km sur cette période."

    return "Je peux te faire un résumé ou des statistiques 🙂"
