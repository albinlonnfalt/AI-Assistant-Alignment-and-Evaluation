# Run Evaluation

## Insert Data

Place your AI Assistant's answered data into the `run_evals/data/input` folder. By default, the data should include columns named 'question', 'answer', and 'context'. While you can rename these columns, doing so will require code modifications.

## Execute

It is recommended to run the evaluation script using the Python debugger. The `launch.json` file contains a configuration named "Run eval" with default arguments. You can use this as a template to get started.