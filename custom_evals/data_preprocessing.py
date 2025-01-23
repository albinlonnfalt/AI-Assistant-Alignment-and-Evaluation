import json
import argparse
import re

def save_jsonl(data, file_path):
    with open(file_path, 'w', encoding='utf-8', errors='ignore') as file:
        for item in data:
            file.write(json.dumps(item, ensure_ascii=False) + '\n')

def read_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            data.append(json.loads(line.strip()))
    return data

def remove_unwanted_characters(text):
    # Remove literal \uXXXX sequences
    text = re.sub(r'\\u[0-9A-Fa-f]{4}', '', text)
    # Decode to Unicode
    decoded = text.encode('raw_unicode_escape').decode('unicode_escape', errors='ignore')
    # Remove any remaining surrogates
    cleaned = re.sub(r'[\uD800-\uDFFF]', '', decoded)
    return cleaned
def data_preprocessing(data_path) -> str:
    processed_data = []
    data = read_jsonl(data_path)
    for item in data:
        try:
            posts_str = json.loads(item.get('social_posts', '[]'))
            posts = json.loads(posts_str)
            for post in posts:
                processed_data.append({
                    #"article": item['response'],
                    "socialmediapost": remove_unwanted_characters(post['socialMediaPost']), # Evaluate sdk does not support surgegates
                })
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for item: {item}, error: {e}")

    output_path = data_path.replace('.jsonl', '_processed.jsonl')
    save_jsonl(processed_data, output_path)
    return output_path


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Evaluate alignment")
    parser.add_argument("--input_path", type=str, help="Path to the input data file", default="custom_evals/data/input_data/eval_data.jsonl")
    args = parser.parse_args()

    input_data_path = args.input_path

    data_preprocessing(input_data_path)
