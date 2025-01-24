from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from evaluator import evaluator
from azure.ai.evaluation import evaluate
import pandas as pd
import json
import os
import prompty.azure
from sklearn.metrics import roc_auc_score
import math
import uuid
import networkx as nx
import matplotlib.pyplot as plt

seed_prompt_path = "custom_evals/evaluator.prompty"

input_data = "custom_evals/data/input_data/evaluator_alignment_data.jsonl"

self_improver_prompt = "custom_evals/self_improver.prompty"

model_config = {
#"azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
#"api_version": os.environ["AZURE_OPENAI_API_VERSION"],
"api_key": os.environ["AZURE_OPENAI_KEY"]
}

class MCTSNode:
    def __init__(self, prompt, value, results_benchmarked, parent=None, mutation_summarization=None):
        self.prompt = prompt
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = value
        self.results_benchmarked = results_benchmarked
        self.mutation_summarization = mutation_summarization

    def add_child(self, child):
        self.children.append(child)
    
    def add_visit(self):
        self.visits += 1

    def get_children(self) -> list:
        return self.children
    
    def get_visits(self):
        return self.visits


class MCTSTree:
    def __init__(self, input_data, root_prompt, value, results_benchmarked, max_expansions=2):
        self.root = MCTSNode(prompt=root_prompt, value=value, results_benchmarked=results_benchmarked)
        self.input_data = input_data
        self.human_labels = get_human_labels(input_data)
        self.max_expansions = max_expansions
        self.expansions= 0

    def _add_child(self, parent_node, child_prompt, value, results_benchmarked):
        child_node = MCTSNode(child_prompt, parent=parent_node, value=value, results_benchmarked=results_benchmarked)
        parent_node.add_child(child_node)
        return child_node
    
    def _select_node(self):
        current_node = self.root
        nodes_traversed = [current_node]
        # traverse down until a leaf node
        while current_node.get_children():
            current_node = self._uct_select(current_node)
            nodes_traversed.append(current_node)
        # Add a visit to all parent nodes to the selected leaf node
        for node in nodes_traversed:
            node.visits += 1
        return current_node
    
    def _uct_select(node: MCTSNode, c=1.41):
        best_child = None
        best_uct_value = -float('inf')
        for child in node.get_children():
            exploitation = child.value
            exploration = c * math.sqrt(math.log(node.get_visits() + 1) / (child.get_visits() + 1))
            uct_value = exploitation + exploration
            if uct_value > best_uct_value:
                best_uct_value = uct_value
                best_child = child
        return best_child
    
    def _expand_node(self, node):
        # Generate new prompts
        new_prompts = sample_new_prompts(node.prompt, node.results_benchmarked, number=2)
        for prompt in new_prompts:
            
            new_prompt_path = f"custom_evals/self_improvment/mutated_prompts/{uuid.uuid4()}.prompty"

            write_to_prompty_file(file_path=new_prompt_path, content=prompt)

            mutation_summarization = get_summarize_mutation_made(parent_prompt=node.prompt, mutated_prompt=new_prompt_path)

            result = get_eval(new_prompt_path, input_data)

            result_benchmarked = compare_to_human_labels(result, self.human_labels)

            auc = get_auc(result_benchmarked)

            leaf_node = MCTSNode(prompt=new_prompt_path, parent=node, value=auc, results_benchmarked=result_benchmarked, mutation_summarization=mutation_summarization)

            self._add_child(parent_node=node, child_prompt=leaf_node, value=auc, results_benchmarked=result_benchmarked)
    
    def _expand_tree(self):
        node = self._select_node()
        self._expand_node(node)

    def _find_best_node(self):
        best_node = self.root
        queue = [self.root]
        while queue:
            current = queue.pop(0)
            if current.value > best_node.value:
                best_node = current
            queue.extend(current.children)
        return best_node
    
    def run_mcts(self):
        while self.expansions < self.max_expansions:
            self._expand_tree()
            self.expansions += 1
        
        return self._find_best_node()


# execute the prompt
def get_eval(prompt_path, data_path):
    evaluate_results = evaluate(
        data=data_path,
        evaluators={
            "eval": evaluator
        },
        evaluator_config={
            "default": {
                "question": "${data.question}",
                "answer": "${data.answer}",
                "context": "${data.context}",
                "prompt_path": prompt_path,
            },
        },
    )

    eval_result = pd.DataFrame(evaluate_results["rows"])

    # Extract 'chain of thought' from the JSON strings
    eval_result['chain of thought'] = eval_result['outputs.eval.output'].apply(lambda x: json.loads(x)['chain of thought'])

    # Extract 'following guidelines'
    eval_result['following guidelines'] = eval_result['outputs.eval.output'].apply(lambda x: json.loads(x)['following guidelines'])

    return eval_result

def write_to_prompty_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

def sample_results(results, number_of_correct_samples=1, number_of_incorrect_samples=1):
    correct = results[results['correct evaluated'] == True]
    incorrect = results[results['correct evaluated'] == False]
    correct_samples = correct.sample(min(number_of_correct_samples, len(correct)))
    incorrect_samples = incorrect.sample(min(number_of_incorrect_samples, len(incorrect)))
    
    samples = pd.concat([correct_samples, incorrect_samples])
    
    return samples.to_json(orient='records')

def load_prompty_as_string(prompt_path):
    with open(prompt_path, 'r') as file:
        prompty_content = file.read()
    return prompty_content

def sample_new_prompts(prompt_to_expand, results, number=2):

    mutated_prompts = []
    for i in range(0, number):
        # execute the prompty file
        result = prompty.execute(
        "self_improver.prompty",  #----- TODO: Fix to a variable -----------
        inputs={
            "prompt": load_prompty_as_string(prompt_to_expand),
            "example_results": sample_results(results, 1, 1)
        },
        configuration=model_config
        )

        result_dict = json.loads(result)

        mutated_prompts.append(result_dict['new prompt'])

    return mutated_prompts

def compare_to_human_labels(results, human_labels):
    results['human_label'] = human_labels
    results['correct evaluated'] = results['following guidelines'] == results['human_label']
    return results

def get_summarize_mutation_made(parent_prompt, mutated_prompt):
    """
    Parameters:
    parent_prompt (str): File path to the prompt of the parent node
    mutated_prompt (str): File path to the prompt of the mutated node
    """

    parent_prompt_content = load_prompty_as_string(parent_prompt)
    mutated_prompt_content = load_prompty_as_string(mutated_prompt)

    # execute the prompty file
    result = prompty.execute(
        "mutation_summarizer.prompty",  #----- TODO: Fix to a variable -----------
        inputs={
            "parent_prompt_content": parent_prompt_content,
            "mutated_prompt_content": mutated_prompt_content
        },
        configuration=model_config
    )

    return result

def get_auc(results):
    return roc_auc_score(results['human_label'], results['following guidelines'])

def get_human_labels(input_data):
    human_labels = []
    with open(input_data, 'r') as file:
        for line in file:
            json_obj = json.loads(line.strip())
            human_label = json_obj["human_label"] == True
            human_labels.append(human_label)
    return human_labels

def plot_mcts_tree(tree):
    G = nx.DiGraph()

    def add_nodes_edges(node):
        label_str = str(node.value)
        if getattr(node, 'mutation_summarization', None):
            label_str += f" [{node.mutation_summarization}]"
        if node not in G:
            G.add_node(node, label=label_str)

        for child in node.get_children():
            child_label_str = str(child.value)
            if getattr(child, 'mutation_summarization', None):
                child_label_str += f" [{child.mutation_summarization}]"
            if child not in G:
                G.add_node(child, label=child_label_str)
            G.add_edge(node, child)
            add_nodes_edges(child)

    add_nodes_edges(tree.root)
    pos = nx.spring_layout(G)
    labels = {n: G.nodes[n]['label'] for n in G.nodes()}
    nx.draw(G, pos, labels=labels, with_labels=True, node_size=5000, node_color='lightblue', arrowsize=20)
    plt.show()


if __name__ == "__main__":

    result = get_eval(seed_prompt_path, input_data)

    human_labels = get_human_labels(input_data)

    result_benchmarked = compare_to_human_labels(result, human_labels)

    auc = get_auc(result_benchmarked)

    mctsTree = MCTSTree(
                    input_data=input_data,
                    root_prompt=seed_prompt_path,
                    value=auc,
                    results_benchmarked=result_benchmarked,
                    max_expansions=2
                )
    
    best_prompt = mctsTree.run_mcts()

    plot_mcts_tree(mctsTree)

    print(best_prompt)

