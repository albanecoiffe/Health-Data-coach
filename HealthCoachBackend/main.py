from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from schemas import ChatRequest
from agent import analyze_question, answer_with_snapshot, factual_response

from datetime import date, timedelta
import calendar

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("❌ ERREUR DE VALIDATION FASTAPI")
    print("BODY :", await request.body())
    print("DETAILS :", exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    print("\n================= CHAT =================")
    print("📝 MESSAGE :", req.message)
    print("📦 SNAPSHOT :", req.snapshot.period.start, "→", req.snapshot.period.end)

    decision = analyze_question(
        req.message, (req.snapshot.period.start, req.snapshot.period.end)
    )

    if (
        "cette semaine" in req.message
        or "semaine en cours" in req.message
        or "semaine actuelle" in req.message
    ):
        # on conserve metric si le LLM l'a donnée
        metric = decision.get("metric") or "DISTANCE"
        decision = {
            "type": "ANSWER_NOW",
            "answer_mode": "FACTUAL",
            "metric": metric,
        }
        print("🛡️ OVERRIDE BACKEND → cette semaine = ANSWER_NOW (FACTUAL)")

    decision_type = decision.get("type", "ANSWER_NOW")
    answer_mode = decision.get("answer_mode")
    metric = decision.get("metric") or "DISTANCE"
    offset = decision.get("offset")

    print("\n================= ROUTING =================")
    print("🧠 DECISION TYPE :", decision_type)
    print("🧠 ANSWER MODE   :", answer_mode)
    print("🧠 METRIC        :", metric)
    print("🧠 OFFSET        :", offset)

    # -------- REQUEST_WEEK --------
    if decision_type == "REQUEST_WEEK":
        offset = int(offset if offset is not None else -1)

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        requested_start = week_start + timedelta(days=7 * offset)
        requested_end = requested_start + timedelta(days=7)

        print("\n📆 CALCUL SEMAINE")
        print("📅 TODAY            :", today)
        print("📅 WEEK_START       :", week_start)
        print("📅 OFFSET           :", offset)
        print("📅 TARGET_WEEK      :", requested_start, "→", requested_end)
        print(
            "📦 SNAPSHOT_CURRENT :",
            req.snapshot.period.start,
            "→",
            req.snapshot.period.end,
        )

        if (
            req.snapshot.period.start == requested_start.isoformat()
            and req.snapshot.period.end == requested_end.isoformat()
        ):
            print("✅ SEMAINE DÉJÀ CHARGÉE → FACTUAL")
            return factual_response(req.snapshot, metric)

        print("🟠 DEMANDE SNAPSHOT SEMAINE")
        return {
            "type": "REQUEST_SNAPSHOT",
            "period": {
                "start": requested_start.isoformat(),
                "end": requested_end.isoformat(),
            },
            "meta": {"metric": metric},
        }

    # -------- REQUEST_MONTH (ABSOLU) --------
    if decision_type == "REQUEST_MONTH":
        month = decision.get("month")
        raw_year = decision.get("year")

        # sécurité: si le LLM renvoie REQUEST_MONTH sans month -> message user-friendly
        if month is None:
            print("⚠️ REQUEST_MONTH sans month → réponse soft")
            return {
                "reply": "Je n’ai pas compris quel mois précis tu voulais. Peux-tu préciser (ex: 'novembre 2025') ?"
            }

        month = int(month)

        if isinstance(raw_year, int):
            year = raw_year
        elif isinstance(raw_year, str) and raw_year.isdigit():
            year = int(raw_year)
        else:
            year = int(req.snapshot.period.start[:4])

        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])

        print("\n📆 CALCUL MOIS (ABSOLU)")
        print("📅 TARGET_MONTH :", start, "→", end)
        print(
            "📦 SNAPSHOT_CURRENT :",
            req.snapshot.period.start,
            "→",
            req.snapshot.period.end,
        )

        if (
            req.snapshot.period.start == start.isoformat()
            and req.snapshot.period.end == end.isoformat()
        ):
            print("✅ MOIS DÉJÀ CHARGÉ → FACTUAL")
            return factual_response(req.snapshot, metric)

        print("🟠 DEMANDE SNAPSHOT MOIS (ABSOLU)")
        return {
            "type": "REQUEST_SNAPSHOT",
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "meta": {"metric": metric},
        }

    # -------- REQUEST_MONTH_RELATIVE --------
    if decision_type == "REQUEST_MONTH_RELATIVE":
        raw_offset = decision.get("offset")
        # 🔒 VERROU SÉMANTIQUE
        msg = req.message.lower()
        if "ce mois" in msg:
            offset = 0
        elif "mois dernier" in msg:
            offset = -1
        else:
            offset = int(raw_offset or -1)

        today = date.today()  # ⚠️ doit être TODAY, pas basé sur snapshot
        target_month = today.month + offset
        target_year = today.year

        while target_month < 1:
            target_month += 12
            target_year -= 1
        while target_month > 12:
            target_month -= 12
            target_year += 1

        start = date(target_year, target_month, 1)
        end = date(
            target_year, target_month, calendar.monthrange(target_year, target_month)[1]
        )

        print("\n📆 CALCUL MOIS (RELATIF)")
        print("📅 TODAY            :", today)
        print("📅 OFFSET           :", offset)
        print("📅 TARGET_MONTH     :", start, "→", end)
        print(
            "📦 SNAPSHOT_CURRENT :",
            req.snapshot.period.start,
            "→",
            req.snapshot.period.end,
        )

        if (
            req.snapshot.period.start == start.isoformat()
            and req.snapshot.period.end == end.isoformat()
        ):
            print("✅ MOIS RELATIF DÉJÀ CHARGÉ → FACTUAL")
            return factual_response(req.snapshot, metric)

        print("🟠 DEMANDE SNAPSHOT MOIS RELATIF")
        return {
            "type": "REQUEST_SNAPSHOT",
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "meta": {"metric": metric},
        }

    # -------- ANSWER_NOW --------
    print("\n📊 DONNÉES SNAPSHOT")
    print("📏 DISTANCE :", req.snapshot.totals.distance_km)
    print("⏱️ DURÉE    :", req.snapshot.totals.duration_min)
    print("📆 SÉANCES  :", req.snapshot.totals.sessions)

    if answer_mode == "FACTUAL":
        print("🟢 RÉPONSE FACTUELLE")
        return factual_response(req.snapshot, metric)

    print("🟢 RÉPONSE LLM (COACHING/SMALL TALK)")
    return {"reply": answer_with_snapshot(req.message, req.snapshot)}
