# Rôle : point d’entrée de l’API
# Ce fichier : démarre FastAPI, expose /chat, reçoit les JSON venant de l’app, délègue toute l’intelligence au router


from fastapi import FastAPI
from schemas import ChatRequest
from coach.router import handle_chat


app = FastAPI()


@app.post("/chat")
def chat(req: ChatRequest):
    return handle_chat(req)
