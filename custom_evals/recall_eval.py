import json
import os
from typing import TypedDict
import prompty
# to use the azure invoker make
# sure to install prompty like this:
# pip install prompty[azure]
import prompty.azure
from dotenv import load_dotenv


load_dotenv()

# pylint: disable=C0115
class recall_eval(TypedDict):
    aligned: str
    reason: str

def marketing_eval(  
      question: str,
      answer: str,
      context: str,
      #human_label # Only for develpment. Remove later
) -> MarketingEvalOutput:
    """
    Evaluates the appropriateness of a marketing response based on the given question, answer, and context.
    Args:
      question (str): The marketing-related question being addressed.
      answer (str): The response provided to the marketing question.
      context (str): Additional context or background information relevant to the marketing scenario.
    Returns:
      MarketingEvalOutput: The result of the evaluation, indicating whether the marketing response is appropriate.
    """

  # execute the prompty file
    model_config = {
        #"azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
        #"api_version": os.environ["AZURE_OPENAI_API_VERSION"],
        "api_key": os.environ["AZURE_OPENAI_KEY"]
    }

    result = prompty.execute(
        "detect_inapproperate_marketing.prompty", 
        inputs={
          "question": question,
          "answer": answer,
          "context": context
        },
        configuration=model_config
    )

    return result

