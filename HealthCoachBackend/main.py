from fastapi import FastAPI
from schemas import ChatRequest
from coach.router import handle_chat


app = FastAPI()


@app.post("/chat")
def chat(req: ChatRequest):
    return handle_chat(req)
