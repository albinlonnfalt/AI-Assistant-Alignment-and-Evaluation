import json

def find_problematic_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, start=1):
            try:
                json_obj = json.loads(line)
                json.dumps(json_obj, ensure_ascii=False).encode('utf-8')
            except UnicodeEncodeError as e:
                print(f"UnicodeEncodeError on line {line_number}: {e}")
                print(f"Problematic JSONL object: {line}")
                break

file_path = 'c:/Users/albinlnnflt/OneDrive - Microsoft/Customer/scale_ai/AI-Assistant-Alignment-and-Evaluation/custom_evals/data/input_data/eval_data_processed_human_label.jsonl'
find_problematic_jsonl(file_path)
print('done')