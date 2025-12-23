# Rôle : règles métier
# Exemples : comment formuler un résumé, comment comparer deux périodes, quelles stats afficher selon l’intent
# Pas de NLP
# Pas d’API
# Juste de la logique pure


from coach.intent_parser import Intent
from models import WeeklySnapshot


def generate_reply(intent: Intent, snapshot: WeeklySnapshot) -> str:
    if intent == Intent.SUMMARY:
        return summary_reply(snapshot)

    if intent == Intent.STATS:
        return stats_reply(snapshot)

    if intent == Intent.COMPARE:
        return compare_reply(snapshot)

    return fallback_reply()


def summary_reply(snapshot: WeeklySnapshot) -> str:
    t = snapshot.totals

    if t.sessions == 0:
        return "Tu n’as effectué aucune séance sur cette période."

    return (
        f"Sur cette période, tu as couru {t.distance_km:.1f} km "
        f"en {t.sessions} séance{'s' if t.sessions > 1 else ''}, "
        f"pour un total de {int(t.duration_min)} minutes."
    )


def stats_reply(snapshot: WeeklySnapshot) -> str:
    t = snapshot.totals

    if t.sessions == 0:
        return "Aucune activité enregistrée sur cette période."

    return (
        f"Tu as parcouru {t.distance_km:.1f} km "
        f"répartis sur {t.sessions} séance{'s' if t.sessions > 1 else ''}."
    )


def compare_reply(snapshot: WeeklySnapshot) -> str:
    return (
        "La comparaison est en cours de développement. Elle sera bientôt disponible 😊"
    )


def fallback_reply() -> str:
    return (
        "Je peux te faire un résumé, te donner des statistiques "
        "ou comparer des périodes. Que veux-tu savoir ?"
    )
