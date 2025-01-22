from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from .data_generator import generate_data

app = FastAPI()
load_dotenv()

class AgentDefinition(BaseModel):
    type: str
    description: str

class GenerateInputRequest(BaseModel):
    topics: list
    tones: list
    instructions: list
    languages: list
    context: str
    number_of_generated_rows: int
    agent_definitions: list[AgentDefinition] = None

@app.post("/api/generate")
async def generate_input(request: GenerateInputRequest):
    #Align the key names with the data generator
    for collection in [request.topics, request.tones, request.instructions, request.languages]:
        for item in collection:
            if 'frequencyScore' in item:
                item['frequency score'] = item.pop('frequencyScore')
            if 'additionalInstruction' in item:
                item['additional instruction'] = item.pop('additionalInstruction')
    generated_data = generate_data(
        request.topics,
        request.tones,
        request.instructions,
        request.languages,
        request.context,
        request.number_of_generated_rows,
        request.agent_definitions
        
    )
    return generated_data