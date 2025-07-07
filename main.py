from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

@app.post("/ask")
def ask_endpoint(data: PromptRequest):
    return {"reply": f"You said: {data.prompt}"}
