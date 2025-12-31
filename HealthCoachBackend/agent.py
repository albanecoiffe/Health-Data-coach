import json
from datetime import date, timedelta
from llm import call_ollama

SYSTEM_COACH_PROMPT = """
Tu es un coach de course à pied intelligent et professionnel.

RÈGLES STRICTES :
- Tu analyses les données UNIQUEMENT si la question de l'utilisateur est claire et explicite.
- Si le message est vague, ambigu ou une simple salutation
  (ex: "hello", "salut", "bonjour", "ok", "ça va ?"),
  tu NE DOIS PAS analyser les statistiques.
- Dans ce cas, tu dois répondre brièvement
  en demandant ce que l'utilisateur souhaite analyser.
- Si la période déjà fournie CORRESPOND EXACTEMENT à la période demandée
  retourne ANSWER_NOW.


Exemples de questions claires :
- "Est-ce que je cours trop vite ?"
- "Fais-moi un résumé de la semaine"
- "Est-ce que je progresse ?"

Exemples de réponses attendues si la question est vague :
- "Salut 👋 Que veux-tu analyser : ton rythme, ton volume ou ta récupération ?"
- "Dis-moi ce que tu aimerais comprendre sur tes entraînements."

Sois concis, clair et bienveillant.
Ne fais jamais d'analyse spontanée sans intention explicite.
"""

import json
from llm import call_ollama


def analyze_question(message: str, current_period: tuple[str, str]) -> dict:
    start, end = current_period
    print("\n================= ANALYZE_QUESTION =================")
    print("📝 MESSAGE UTILISATEUR :", repr(message))
    print("📅 PÉRIODE COURANTE   :", start, "→", end)

    prompt = f"""
Tu es un moteur de décision STRICT pour une application de suivi de course à pied.

Tu dois retourner UNE décision JSON valide, et RIEN d'autre.

========================================
1️⃣ PRIORITÉ ABSOLUE — SMALL TALK
========================================

Si le message est une salutation ou une phrase vague
(ex: "hello", "salut", "bonjour", "ça va", "merci", "ok") :

Retourne EXACTEMENT :
{{
  "type": "ANSWER_NOW",
  "answer_mode": "SMALL_TALK"
}}

Tu n’as PAS le droit de demander un snapshot dans ce cas.

========================================
2️⃣ CHANGEMENT DE PÉRIODE — SEMAINES
========================================

Si la question contient :

- "semaine dernière" → offset = -1
- "il y a X semaines" → offset = -X

Retourne :
{{
  "type": "REQUEST_WEEK",
  "offset": -X,
  "metric": "<métrique détectée>"
}}

⚠️ Même si la question parle de km, durée, séances, etc.

----------------------------------------
SEMAINE COURANTE
----------------------------------------

Si la question contient exactement :
- "cette semaine"
- "la semaine actuelle"

Retourne :
{{
  "type": "ANSWER_NOW",
  "answer_mode": "FACTUAL",
  "metric": "<métrique détectée>"
}}

========================================
3️⃣ CHANGEMENT DE PÉRIODE — MOIS RELATIFS (PRIORITÉ ABSOLUE)
========================================

Si la question contient EXACTEMENT :

- "ce mois-ci"
- "ce mois ci"

ALORS tu DOIS retourner EXACTEMENT :

{{
  "type": "REQUEST_MONTH_RELATIVE",
  "offset": 0,
  "metric": "<metric détectée>"
}}

Si la question contient EXACTEMENT :

- "le mois dernier"
- "mois dernier"

ALORS tu DOIS retourner EXACTEMENT :

{{
  "type": "REQUEST_MONTH_RELATIVE",
  "offset": -1,
  "metric": "<metric détectée>"
}}

Si la question contient :

- "il y a X mois"

ALORS tu DOIS retourner :

{{
  "type": "REQUEST_MONTH_RELATIVE",
  "offset": -X,
  "metric": "<metric détectée>"
}}

⚠️ Tu n’as PAS le droit :
- d’inverser les offsets
- de retourner REQUEST_WEEK
- de retourner ANSWER_NOW


========================================
4️⃣ MOIS ABSOLU (EXPLICITE SEULEMENT)
========================================

Si (et seulement si) un mois explicite est mentionné
(janvier → décembre) :

Retourne :
{{
  "type": "REQUEST_MONTH",
  "month": 1-12,
  "year": YYYY ou null,
  "metric": "<métrique détectée>"
}}

========================================
5️⃣ ANSWER_NOW FACTUEL
========================================

Si la question demande une valeur mesurable
(distance, km, durée, temps, séances, FC, allure, dénivelé) :

Retourne :
{{
  "type": "ANSWER_NOW",
  "answer_mode": "FACTUAL",
  "metric": "<métrique détectée>"
}}

========================================
6️⃣ PAR DÉFAUT
========================================

Retourne :
{{
  "type": "ANSWER_NOW",
  "answer_mode": "COACHING"
}}

========================================
MÉTRIQUES POSSIBLES
========================================

DISTANCE | DURATION | SESSIONS | AVG_HR | PACE | ELEVATION | LOAD | UNKNOWN

========================================
QUESTION
========================================
{message}

========================================
PÉRIODE COURANTE
========================================
{start} → {end}
"""

    raw = call_ollama(prompt)

    print("\n📥 RÉPONSE BRUTE DU LLM :")
    print(raw)

    try:
        data = safe_parse_json(raw)
        if not data or "type" not in data:
            print("⚠️ JSON non exploitable → fallback contrôlé")
            return {"type": "ANSWER_NOW", "answer_mode": "SMALL_TALK"}
        print("\n📦 JSON PARSÉ :", data)

        if not isinstance(data, dict) or "type" not in data:
            print("⚠️ JSON invalide → fallback SMALL_TALK")
            return {"type": "ANSWER_NOW", "answer_mode": "SMALL_TALK"}

        return data

    except Exception as e:
        print("❌ ERREUR JSON :", e)
        print("➡️ fallback SMALL_TALK")
        return {"type": "ANSWER_NOW", "answer_mode": "SMALL_TALK"}


def answer_with_snapshot(message: str, snapshot) -> str:
    prompt = f"""
Tu es un coach de course à pied humain et bienveillant.

RÈGLES :
- Small talk → réponse courte, aucune statistique
- Coaching → tu peux utiliser les données ci-dessous
- Ne fais AUCUN calcul
- Ne modifies AUCUN chiffre

DONNÉES :
- Distance : {snapshot.totals.distance_km}
- Séances : {snapshot.totals.sessions}
- Durée : {snapshot.totals.duration_min}
- Charge ratio : {snapshot.training_load.ratio if snapshot.training_load else "N/A"}

Question :
{message}
"""
    return call_ollama(prompt)


def factual_response(snapshot, metric: str) -> dict:
    start = snapshot.period.start
    end = snapshot.period.end

    # Aucune séance
    if snapshot.totals.sessions == 0:
        return {
            "reply": f"Aucune séance enregistrée sur la période du {start} au {end}."
        }

    metric = metric.upper()

    if metric == "DISTANCE":
        return {
            "reply": (
                f"Sur la période du {start} au {end}, "
                f"tu as couru {round(snapshot.totals.distance_km, 1)} km."
            )
        }

    if metric == "DURATION":
        minutes = round(snapshot.totals.duration_min)
        hours = minutes // 60
        mins = minutes % 60

        if hours > 0:
            return {
                "reply": (
                    f"Sur la période du {start} au {end}, "
                    f"tu as couru pendant {hours}h{mins:02d}."
                )
            }
        else:
            return {
                "reply": (
                    f"Sur la période du {start} au {end}, "
                    f"tu as couru pendant {minutes} minutes."
                )
            }

    if metric == "SESSIONS":
        return {
            "reply": (
                f"Sur la période du {start} au {end}, "
                f"tu as effectué {snapshot.totals.sessions} séances."
            )
        }

    # Fallback propre
    return {
        "reply": (
            f"Sur la période du {start} au {end}, "
            f"tu as {snapshot.totals.sessions} séances pour "
            f"{round(snapshot.totals.distance_km, 1)} km."
        )
    }


def safe_parse_json(raw: str) -> dict | None:
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return None
