import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import argparse
from azure.ai.evaluation import evaluate

from custom_evals.marketing_eval import marketing_eval

import json

# If you want to use Azure AI Foundry
"""
azure_ai_project = {
    "subscription_id": "xx",
    "resource_group_name": "xx",
    "project_name": "xx",
}
"""

# Define a mapping of evaluator names to functions
evaluators = {
    'marketing_eval': marketing_eval,
    # Add more evaluators here
}

# Parse the string column into dictionaries
def safe_json_loads(x):
    try:
        return json.loads(x)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e} for input: {x}")
        return None


def run_evaluate(args):

    # Select evaluator
    evaluator = evaluators.get(args.evaluator)

    ## Run eval ##

    try:
        result_eval = evaluate(
            data=args.input_path,
            evaluators={
                "evaluator": evaluator,
            },
            evaluator_config={
                "evaluator": {
                    "question": "${data.question}",
                    "answer": "${data.answer}",
                    "context": "${data.context}",
                },
            },
            #azure_ai_project=azure_ai_project
        )
    except Exception as e:
        print(f"An error occurred during evaluation: {e}")
        result_eval = {"rows": []}


    ## Parse the results ##

    df = pd.DataFrame(result_eval["rows"])

    print(f"Number of rows in 'outputs.evaluator.output': {len(df)}")

    # Drop null values
    null_count = df['outputs.evaluator.output'].isnull().sum()
    print(f"Number of nulls in 'outputs.evaluator.output': {null_count}")
    df = df.dropna(subset=['outputs.evaluator.output'])

    # Parse the string column into dictionaries
    df['parsed'] = df['outputs.evaluator.output'].apply(safe_json_loads)
    df = df.dropna(subset=['parsed'])

    # Create new columns
    df['chain of thought'] = df['parsed'].apply(lambda x: x['chain of thought'])
    df['following guidelines'] = df['parsed'].apply(lambda x: x['following guidelines'])

    # Save entier dataset with flaged 
    df.to_csv(args.output_path, index=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate qa bank.')
    parser.add_argument('--evaluator', type=str, choices=['marketing_eval'], required=True, help='Name of the evaluator to use')
    parser.add_argument('--output_path', type=str, required=True, help='Path to save the evaluation results as a CSV file')
    parser.add_argument('--input_path', type=str, required=True, help='Path to input data')

    args = parser.parse_args()

    run_evaluate(args)