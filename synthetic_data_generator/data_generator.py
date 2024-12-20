from dotenv import load_dotenv
load_dotenv()

import json
import os
import prompty
# import invoker
import prompty.azure
import time

import random
import numpy as np
import argparse

from azure.identity import DefaultAzureCredential


# Read config
config_path = os.path.join(os.path.dirname(__file__), 'config/response_lengh_distrubution.json')
with open(config_path, 'r') as file:
    config = json.load(file)
mean = config['mean']
sigma = config['sigma']
shift = config['shift']


def generate_question(topic, tone, language, additional_instructions, context, question_length, model_config):
    
    result = prompty.execute(
        "data_generator.prompty", 
        inputs={
            "topic": topic,
            "tone": tone,
            "language": language,
            "additional_instructions": additional_instructions,
            "context": context,
            "question_length": question_length
        },
        configuration=model_config
    )

    return result

def write_json_file(file_path, data):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_data = json.load(file)
                if not isinstance(existing_data, list):
                    existing_data = []
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_data.append(data)

    with open(file_path, 'w') as file:
        json.dump(existing_data, file, indent=4)


def load_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def normalize_scores(items):
    total_score = sum(item['frequency score'] for item in items)
    for item in items:
        item['normalized score'] = item['frequency score'] / total_score
    return items

def draw_item(items, key):
    normalized_scores = [item['normalized score'] for item in items]
    chosen_item = random.choices(items, weights=normalized_scores, k=1)[0]
    return chosen_item[key]

# Generate the question lenght by drawing from a distrubution
def generate_response_length():
    # Generate a log-normally distributed number and shift
    length = np.random.lognormal(mean=mean, sigma=sigma) + shift
    # Ensure the number is at least the shift
    return int(max(shift, length))


def generate_data(topics, tones, additional_instructions, languages, context_string, number_of_rows):
    topics = normalize_scores(topics)
    tones = normalize_scores(tones)
    additional_instructions = normalize_scores(additional_instructions)
    languages = normalize_scores(languages)
    results = []
    for i in range(number_of_rows):
        topic = draw_item(topics, "topic")
        tone = draw_item(tones, "tone")
        language = draw_item(languages, "language")
        additional_instruction = draw_item(additional_instructions, "additional instruction")
        question_length = generate_response_length()
    
        print(question_length)

        question = generate_question(
            topic,
            tone,
            language,
            additional_instruction,
            context_string,
            question_length,
            model_config={
                "api_key": os.environ["AZURE_OPENAI_KEY"]
            }
        )
        results.append(question)

        # Avoid rate limiting
        time.sleep(1)
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate synthetic data.')
    parser.add_argument('--topics_file', type=str, required=True, help='Path to the topics JSON file')
    parser.add_argument('--tones_file', type=str, required=True, help='Path to the tones JSON file')
    parser.add_argument('--instructions_file', type=str, required=True, help='Path to the additional instructions JSON file')
    parser.add_argument('--languages_file', type=str, required=True, help='Path to the languages JSON file')
    parser.add_argument('--context_file', type=str, required=True, help='Path to the context text file')
    parser.add_argument('--number_of_generated_rows', type=int, required=True, help='Number of rows to generate')
    parser.add_argument('--output_file', type=str, required=True, help='Path to the output JSON file')

    args = parser.parse_args()

    topics = load_json_file(args.topics_file)
    tones = load_json_file(args.tones_file)
    additional_instructions = load_json_file(args.instructions_file)
    languages = load_json_file(args.languages_file)
    with open(args.context_file, 'r') as file:
        context_string = file.read()



    results = generate_data(
        topics,
        tones,
        additional_instructions,
        languages,
        context_string,
        args.number_of_generated_rows
    )
    write_json_file(args.output_file, results)