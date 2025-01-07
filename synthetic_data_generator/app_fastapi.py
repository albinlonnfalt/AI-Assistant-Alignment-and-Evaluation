from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from .data_generator import generate_data

app = FastAPI()
load_dotenv()

class GenerateInputRequest(BaseModel):
    topics: list
    tones: list
    instructions: list
    languages: list
    context: str
    number_of_generated_rows: int

@app.post("/generate")
async def generate_input(request: GenerateInputRequest):
    generated_data = generate_data(
        request.topics,
        request.tones,
        request.instructions,
        request.languages,
        request.context,
        request.number_of_generated_rows
    )
    return generated_data