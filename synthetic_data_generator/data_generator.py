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

def generate_question(chunk, chunk_id, sampled_items, context, question_length, model_config, output_file):
    """
    Generates a question based on the provided parameters and writes the result to a JSON file.
    Args:
        sampled_items (dict): A dictionary containing the sampled items from the injection data.
        context (str): The context or background information for the question.
        question_length (int): The desired length of the question.
        model_config (dict): Configuration settings for the model used to generate the question.
        output_file (str): The file path where the generated question will be saved in JSON format.
    Returns:
        None
    """

    sampled_items_packaged = package_sampled_items(sampled_items)
    
    result = prompty.execute(
        "data_generator.prompty", 
        inputs={
            "sampled_items": sampled_items_packaged,
            "context": context,
            "question_length": question_length,
            "chunk": chunk
        },
        configuration=model_config
    )

    write_json_file(output_file, {"question": result, "correct_chunk": chunk_id})

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


def package_sampled_items(sampled_items) -> str:
    """
    Packages the sampled items into a single string for use in the question generation process.

    Args:
        sampled_items (dict): A dictionary containing the sampled items from the injection data.

    Returns:
        str: A formatted string containing the sampled items.
    """
    # Create a formatted string containing the sampled items
    formatted_items = "\n\n - ".join([f"{key}: {value}" for key, value in sampled_items.items()])
    return formatted_items

def load_json_file(file_path):
    """
    Load data from a JSON file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        data (dict): The data loaded from the JSON file.
        filename_no_ext (str): The filename without the extension
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        filename_no_ext = os.path.splitext(os.path.basename(file_path))[0]
    return data, filename_no_ext


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

def sample_item(items, key):
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

def loop_files_in_folder(folder_path):
    """
    Generator function that yields the full path of each file in the specified folder.

    Args:
        folder_path (str): The path to the folder containing the files.

    Yields:
        str: The full path of each file in the folder.
    """
    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)
        if os.path.isfile(full_path):
            yield full_path

def sample_chunks(file_path):
    """
    Load data from a JSON file and sample a chunk from the list of items.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: A dictionary containing the sampled chunk.
    """
    data, _ = load_json_file(file_path)

    sampled = random.choice(data)

    return sampled["content"], sampled["chunk_id"]


def generate_data(chunk_path, injection_folder_path, context_file_path, length_config_file, number_of_generated_rows, output_file_path):
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
        "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
        "api_key": os.getenv("AZURE_OPENAI_KEY")
    }

    # Try to read the content of the context file, set to empty string if not found
    try:
        with open(context_file_path, 'r', encoding='utf-8') as file:
            context_string = file.read()
    except FileNotFoundError:
        context_string = ""

    injection_generator = loop_files_in_folder(injection_folder_path)

    injection_data = {}
    for injection_file in injection_generator:
        data, filename_no_ext = load_json_file(injection_file)
        data_normalized = normalize_scores(data)
        injection_data[filename_no_ext] = data_normalized

    # --Response length config--
    mean, sigma, shift = get_response_lenght_config(length_config_file)

    for _ in range(int(number_of_generated_rows)):
        sampled_items = {}
        for key, value in injection_data.items():
            sampled_items[key] = sample_item(value, key)

        question_length = generate_response_length(mean=mean, sigma=sigma, shift=shift)

        chunk, chunk_id = sample_chunks(chunk_path)

        generate_question(chunk, chunk_id, sampled_items, context_string, question_length, model_config, output_file_path)

        # Avoid rate limiting
        time.sleep(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate synthetic data.')
    parser.add_argument('--chunk_path', type=str, required=True, help='Path to the folder containing the files of injections')
    parser.add_argument('--injection_folder_path', type=str, required=True, help='Path to the folder containing the files of injections')
    parser.add_argument('--context_file_path', type=str, required=False, help='Path to the file containing the context')
    parser.add_argument('--length_config_file', type=str, required=True, help='Path to config for response length')
    parser.add_argument('--number_of_generated_rows', type=int, required=True, help='Number of rows to generate')
    parser.add_argument('--output_file_path', type=str, required=True, help='Path to output file')

    args = parser.parse_args()

    generate_data(
        chunk_path = args.chunk_path,
        injection_folder_path=args.injection_folder_path,
        context_file_path=args.context_file_path,
        length_config_file=args.length_config_file,
        number_of_generated_rows=args.number_of_generated_rows,
        output_file_path=args.output_file_path
    )