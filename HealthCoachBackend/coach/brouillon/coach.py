# coach.py


def generate_coach_reply(user_message, stats):
    """
    stats = {
        "distance": 20.5,
        "sessions": 3,
        "avg_hr": 152,
        "zones": {"Z1": 10, "Z2": 15, "Z3": 8, "Z4": 4, "Z5": 1}
    }
    """

    msg = user_message.lower()

    # Exemple de règles simples (à enrichir)
    if "fatigue" in msg or "crevé" in msg:
        return (
            "Je comprends, baisse un peu l’intensité aujourd’hui. Priorité à Z1/Z2 👍"
        )

    if "progress" in msg or "progrès" in msg or "ameliorer" in msg:
        return "Tu progresses bien ! Continue d’augmenter la Z3 progressivement."

    # Coach basé sur les stats
    if stats:
        distance = stats["distance"]
        sessions = stats["sessions"]
        hr = stats["avg_hr"]

        response = (
            f"Cette semaine tu as couru {distance:.1f} km en {sessions} séances. "
            f"Ta FC moyenne est {hr} bpm. "
        )

        if hr > 165:
            response += "⚠️ Tu cours un peu trop haut en FC, pense à faire plus de Z2."
        elif hr < 140:
            response += "👍 Belle endurance fondamentale cette semaine !"

        return response

    return "Merci pour ton message ! Comment s’est passée ta séance ?"
