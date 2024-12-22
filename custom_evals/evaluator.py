import json
import os
import prompty
# to use the azure invoker make 
# sure to install prompty like this:
# pip install prompty[azure]
import prompty.azure
from prompty.tracer import trace, Tracer, console_tracer, PromptyTracer
from dotenv import load_dotenv
load_dotenv()
from typing import TypedDict

class EvalOutput(TypedDict):
  aligned: str
  reason: str

@trace
def evaluator(    
  question: str,
  answer: str,
  context: str,
  prompt_path: str = "evaluator.prompty",
  #human_label # Only for develpment. Remove later
) -> EvalOutput:

  # execute the prompty file
  model_config = {
    #"azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
    #"api_version": os.environ["AZURE_OPENAI_API_VERSION"],
    "api_key": os.environ["AZURE_OPENAI_KEY"]
  }

  result = prompty.execute(
    prompt_path, 
    inputs={
      "question": question,
      "answer": answer,
      "context": context
    },
    configuration=model_config
  )

  return result

