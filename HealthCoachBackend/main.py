from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from services.snapshots import load_snapshots_for_comparison
from services.periods import period_to_dates
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

    # ======================================================
    # 🔴 COMPARAISON FINALE — PRIORITÉ ABSOLUE
    # ⚠️ Si snapshots + meta sont présents → PAS DE LLM
    # ======================================================
    if req.snapshots is not None and req.meta is not None:
        print("🟢 COMPARAISON FINALE — SNAPSHOTS PRÉSENTS")

        left = req.snapshots.left
        right = req.snapshots.right
        metric = req.meta.get("metric", "DISTANCE")

        from services.comparisons import compare_snapshots

        diff = compare_snapshots(left, right, metric)

        if diff > 0:
            trend = "plus"
        elif diff < 0:
            trend = "moins"
        else:
            trend = "autant"

        return {
            "reply": (
                f"Tu as couru {trend} de distance cette semaine "
                f"que la semaine dernière."
            )
        }

    # ======================================================
    # 🔵 SINON → FLOW NORMAL (LLM AUTORISÉ)
    # ======================================================
    print(
        "📦 SNAPSHOT :",
        req.snapshot.period.start,
        "→",
        req.snapshot.period.end,
    )

    decision = analyze_question(
        req.message,
        (req.snapshot.period.start, req.snapshot.period.end),
    )

    # 🛡️ VERROU BACKEND — cette semaine = FACTUAL
    if decision.get("type") == "ANSWER_NOW" and (
        "cette semaine" in req.message.lower()
        or "semaine en cours" in req.message.lower()
        or "semaine actuelle" in req.message.lower()
    ):
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

    # ======================================================
    # 🟠 REQUEST_WEEK
    # ======================================================
    if decision_type == "REQUEST_WEEK":
        offset = int(offset if offset is not None else -1)

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        requested_start = week_start + timedelta(days=7 * offset)
        requested_end = requested_start + timedelta(days=7)

        print("\n📆 CALCUL SEMAINE")
        print("📅 TARGET_WEEK :", requested_start, "→", requested_end)

        if (
            req.snapshot.period.start == requested_start.isoformat()
            and req.snapshot.period.end == requested_end.isoformat()
        ):
            print("✅ SEMAINE DÉJÀ CHARGÉE → FACTUAL")
            return factual_response(req.snapshot, metric)

        return {
            "type": "REQUEST_SNAPSHOT",
            "period": {
                "start": requested_start.isoformat(),
                "end": requested_end.isoformat(),
            },
            "meta": {"metric": metric},
        }

    # ======================================================
    # 🟠 REQUEST_MONTH (ABSOLU)
    # ======================================================
    if decision_type == "REQUEST_MONTH":
        month = decision.get("month")
        raw_year = decision.get("year")

        if month is None:
            return {
                "reply": (
                    "Je n’ai pas compris quel mois précis tu voulais. "
                    "Peux-tu préciser (ex: 'novembre 2025') ?"
                )
            }

        month = int(month)
        year = (
            int(raw_year)
            if isinstance(raw_year, int)
            else int(req.snapshot.period.start[:4])
        )

        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])

        if (
            req.snapshot.period.start == start.isoformat()
            and req.snapshot.period.end == end.isoformat()
        ):
            print("✅ MOIS DÉJÀ CHARGÉ → FACTUAL")
            return factual_response(req.snapshot, metric)

        return {
            "type": "REQUEST_SNAPSHOT",
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "meta": {"metric": metric},
        }

    # ======================================================
    # 🟠 REQUEST_MONTH_RELATIVE
    # ======================================================
    if decision_type == "REQUEST_MONTH_RELATIVE":
        raw_offset = decision.get("offset")
        msg = req.message.lower()

        if "ce mois" in msg:
            offset = 0
        elif "mois dernier" in msg:
            offset = -1
        else:
            offset = int(raw_offset or -1)

        today = date.today()
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
            target_year,
            target_month,
            calendar.monthrange(target_year, target_month)[1],
        )

        if (
            req.snapshot.period.start == start.isoformat()
            and req.snapshot.period.end == end.isoformat()
        ):
            print("✅ MOIS RELATIF DÉJÀ CHARGÉ → FACTUAL")
            return factual_response(req.snapshot, metric)

        return {
            "type": "REQUEST_SNAPSHOT",
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "meta": {"metric": metric},
        }

    # ======================================================
    # 🟣 COMPARE_PERIODS → DEMANDE SNAPSHOTS
    # ======================================================
    if decision_type == "COMPARE_PERIODS":
        left_start, left_end = period_to_dates(decision["left"])
        right_start, right_end = period_to_dates(decision["right"])

        return {
            "type": "REQUEST_SNAPSHOT_BATCH",
            "snapshots": {
                "left": {
                    "start": left_start.isoformat(),
                    "end": left_end.isoformat(),
                },
                "right": {
                    "start": right_start.isoformat(),
                    "end": right_end.isoformat(),
                },
            },
            "meta": {
                "metric": decision["metric"],
                "comparison": f"{decision['left']}_VS_{decision['right']}",
            },
        }

    # ======================================================
    # 🟢 ANSWER_NOW
    # ======================================================
    if answer_mode == "FACTUAL":
        return factual_response(req.snapshot, metric)

    return {"reply": answer_with_snapshot(req.message, req.snapshot)}
