import json
import os
import time
import random
import argparse
import numpy as np
import prompty
import prompty.azure
from dotenv import load_dotenv
load_dotenv()

def generate_question(topic, tone, language, additional_instructions, context, question_length, model_config, output_file):
    """
    Generates a question based on the provided parameters and writes the result to a JSON file.
    Args:
        topic (str): The topic of the question.
        tone (str): The tone of the question (e.g., formal, informal).
        language (str): The language in which the question should be generated.
        additional_instructions (str): Any additional instructions for generating the question.
        context (str): The context or background information for the question.
        question_length (int): The desired length of the question.
        model_config (dict): Configuration settings for the model used to generate the question.
        output_file (str): The file path where the generated question will be saved in JSON format.
    Returns:
        None
    """
    
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

    write_json_file(output_file, result)

def write_json_file(file_path, data):
    """
    Writes data to a JSON file. If the file already exists and contains a JSON array,
    the new data is appended to the array. If the file does not exist or contains
    invalid JSON, a new array is created with the provided data.
    Args:
        file_path (str): The path to the JSON file.
        data (any): The data to be written to the JSON file. This data will be appended
                    to the existing JSON array or will create a new array if the file
                    does not exist or contains invalid JSON.
    Raises:
        IOError: If there is an error opening or writing to the file.
        json.JSONDecodeError: If there is an error decoding the existing JSON data.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                existing_data = json.load(file)
                if not isinstance(existing_data, list):
                    existing_data = []
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_data.append(data)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, indent=4)


def load_json_file(file_path):
    """
    Load data from a JSON file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The data loaded from the JSON file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def normalize_scores(items: list[dict]) -> list[dict]:
    """
    Normalize the frequency scores of a list of items.

    Each item's 'frequency score' is divided by the total sum of all 'frequency scores' to produce a 'normalized score'.

    Args:
        items (list of dict): A list of dictionaries, each containing a 'frequency score' key.

    Returns:
        list of dict: The input list with an added 'normalized score' key for each dictionary.
    """
    total_score = sum(item['frequency score'] for item in items)
    for item in items:
        item['normalized score'] = item['frequency score'] / total_score
    return items

def draw_item(items, key):
    """
        Selects an item from a list of dictionaries based on their normalized scores and returns the value associated with the given key.

    Args:
        items (list of dict): A list of dictionaries where each dictionary contains a 'normalized score' key.
        key (str): The key whose value needs to be returned from the chosen dictionary.

    Returns:
        The value associated with the specified key from the chosen dictionary.
    """
    normalized_scores = [item['normalized score'] for item in items]
    chosen_item = random.choices(items, weights=normalized_scores, k=1)[0]
    return chosen_item[key]

# Generate the question lenght by drawing from a distrubution
def generate_response_length(mean, sigma, shift) -> int:
    """
    Generate a response length using a log-normal distribution and a shift.
    Parameters:
        mean (float): The mean of the log-normal distribution.
        sigma (float): The standard deviation of the log-normal distribution.
        shift (int): The baseline shift to ensure the minimal length.
        int: The computed response length, guaranteed to be at least the shift value.
    Returns:
        int: The generated response length, which is at least the value of the shift.
    """
    # Generate a log-normally distributed number and shift
    length = np.random.lognormal(mean=mean, sigma=sigma) + shift
    # Ensure the number is at least the shift
    return int(max(shift, length))

def get_response_lenght_config(config_path):
    """
    Retrieves the mean, sigma, and shift values from a JSON configuration file.
    Parameters:
    :param config_path: The path to the JSON configuration file.
    :type config_path: str
    :return: A tuple (mean, sigma, shift) extracted from the configuration.
    :rtype: tuple
    """
    
    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    mean = config['mean']
    sigma = config['sigma']
    shift = config['shift']

    return mean, sigma, shift

def generate_data(args):
    """
    Generates synthetic data based on the provided arguments and configuration.
    Args:
        args (Namespace): A namespace object containing the following attributes:
            context_file (str): Path to the context file.
            topics_file (str): Path to the topics file.
            tones_file (str): Path to the tones file.
            instructions_file (str): Path to the additional instructions file.
            languages_file (str): Path to the languages file.
            number_of_generated_rows (int): Number of rows of data to generate.
            output_file (str): Path to the output file where generated data will be saved.
    Raises:
        KeyError: If required environment variables are not set.
        FileNotFoundError: If any of the specified files do not exist.
        json.JSONDecodeError: If any of the specified files contain invalid JSON.
    Returns:
        None
    """

    # ------ You need environment variables ------
    model_config = {
        #"azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
        #"api_version": os.environ["AZURE_OPENAI_API_VERSION"],
        "api_key": os.environ["AZURE_OPENAI_KEY"]
    }

    # Read the content of the context file
    with open(args.context_file, 'r', encoding='utf-8') as file:
        context_string = file.read()

    # --Topics--
    topics = load_json_file(args.topics_file)
    topics = normalize_scores(topics)

    # --Tones--
    tones = load_json_file(args.tones_file)
    tones = normalize_scores(tones)
    
    # - Additional instructions -
    additional_instructions = load_json_file(args.instructions_file)
    additional_instructions = normalize_scores(additional_instructions)

    # --Languages--
    languages = load_json_file(args.languages_file)
    languages = normalize_scores(languages)

    # --Response length config--
    mean, sigma, shift = get_response_lenght_config(args.length_config_file)

    for _ in range(args.number_of_generated_rows):
        topic = draw_item(topics, "topic")
        tone = draw_item(tones, "tone")
        language = draw_item(languages, "language")
        additional_instruction = draw_item(additional_instructions, "additional instruction")
        question_length = generate_response_length(mean=mean, sigma=sigma, shift=shift)

        generate_question(topic, tone, language, additional_instruction, context_string, question_length, model_config, args.output_file)

        # Avoid rate limiting
        time.sleep(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate synthetic data.')
    parser.add_argument('--topics_file', type=str, required=True, help='Path to the topics JSON file')
    parser.add_argument('--tones_file', type=str, required=True, help='Path to the tones JSON file')
    parser.add_argument('--instructions_file', type=str, required=True, help='Path to the additional instructions JSON file')
    parser.add_argument('--languages_file', type=str, required=True, help='Path to the languages JSON file')
    parser.add_argument('--context_file', type=str, required=True, help='Path to the context text file')
    parser.add_argument('--number_of_generated_rows', type=int, required=True, help='Number of rows to generate')
    parser.add_argument('--output_file', type=str, required=True, help='Path to the output JSON file')
    parser.add_argument('--length_config_file', type=str, required=True, help='Path to config for response length')

    args = parser.parse_args()

    generate_data(args)