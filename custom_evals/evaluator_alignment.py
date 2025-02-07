import argparse
import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from azure.ai.evaluation import evaluate
from sklearn.metrics import cohen_kappa_score
from sklearn.metrics import confusion_matrix
from custom_evals.recall_eval import marketing_eval



def evaluate_alignment(args):
    """
    Evaluates the alignment of the custom evaluator
    Args:
        args (dict): A dictionary of arguments including input data path and other configurations.
    Returns:
        None
    """

    # If you want to use Azure AI Foundry
    """
    azure_ai_project = {
        "subscription_id": "xx",
        "resource_group_name": "xx",
        "project_name": "xx",
    }
    """

    evaluate_results = evaluate(
        data=args.input_path,
        # target=get_response,
        evaluators={
            "eval": marketing_eval,
        },
        evaluator_config={
            "default": {
                "question": "${data.question}",
                "answer": "${data.answer}",
                "context": "${data.context}",
            },
        },
        #azure_ai_project=azure_ai_project
    )

    eval_result = pd.DataFrame(evaluate_results["rows"])

    # Extract 'reason' from the JSON strings
    eval_result['chain of thought'] = eval_result['outputs.eval.output'].apply(lambda x: json.loads(x)['chain of thought'])

    # Extract 'following guidelines'
    eval_result['following guidelines'] = eval_result['outputs.eval.output'].apply(lambda x: json.loads(x)['following guidelines'])

    # Save result to an excel file
    #eval_result.to_excel("data/output/evaluation_results.xlsx", index=False)

    evaluator_labels = eval_result["outputs.eval.output"].apply(lambda x: json.loads(x)["following guidelines"]).to_numpy()

    # Extract human labels to a array
    human_labels = []
    with open(args.input_path, 'r', encoding='utf-8') as file:
        for line in file:
            json_obj = json.loads(line.strip())
            human_label = json_obj["human_label"].strip().lower() == 'true'
            human_labels.append(human_label)

    kappa = cohen_kappa_score(human_labels, evaluator_labels)

    print(f"**Cohen's Kappa: {kappa}**\n\n"
        "Interpreting Cohen’s Kappa:\n"
        "κ < 0.20: Poor agreement\n"
        "κ = 0.21−0.39: Fair agreement\n"
        "κ = 0.40−0.59: Moderate agreement\n"
        "κ = 0.60−0.79: Substantial agreement\n"
        "κ ≥ 0.80: Almost perfect agreement")


    # Calculate the confusion matrix
    cm = confusion_matrix(human_labels, evaluator_labels)

    # Plot the confusion matrix
    plt.figure(figsize=(10, 7))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['False', 'True'], yticklabels=['False', 'True'])
    plt.xlabel('Evaluator Labels')
    plt.ylabel('Human Labels')
    plt.title('Confusion Matrix')
    plt.show()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Evaluate alignment")
    parser.add_argument("--input_path", type=str, help="Path to the input data file", default="custom_evals/data/input_data/evaluator_alignment_data.jsonl")
    args = parser.parse_args()

    evaluate_alignment(args)
