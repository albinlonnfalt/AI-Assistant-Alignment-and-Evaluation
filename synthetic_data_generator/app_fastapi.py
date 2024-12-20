from fastapi import FastAPI, Request
from dotenv import load_dotenv
from .data_generator import generate_data

app = FastAPI()
load_dotenv()

@app.post("/generate")
async def generate_input(request: Request):
    body = await request.json()
    topics = body["topics"]
    tones = body["tones"]
    instructions = body["instructions"]
    languages = body["languages"]
    context_string = body["context"]

    generated_data = generate_data(
        topics,
        tones,
        instructions,
        languages,
        context_string,
        body["number_of_generated_rows"]
    )
    return generated_data