
# Custom Evaluators

This example demonstrates a custom evaluator that leverages model completion. You can also create other types of evaluators, such as those that check if a string contains a specific word. The advantage of using model completion lies in its high flexibility and low development cost.

## Importance of Automatic Evaluators

### Iterative Alignment 

To rapidly iterate on prompts, configurations, or fine-tuned models, it is crucial to have a swift evaluation method to determine if the system has improved. Automatic evaluators can provide near-instant feedback, eliminating the need to rely on human domain experts for daily development tasks. 

### Scale the Evaluation

To effectively cover a significant dataset, it is important to scale the evaluations. Scaling evaluations to a sufficient number of data points often requires automated evaluators that can either operate independently or assist in reducing the number of data points that need to be reviewed by a human.

## Evaluator Alignment

To ensure the reliability of automatic evaluations, it is crucial to align the evaluator with human-annotated data. This alignment guarantees that the evaluation process is trustworthy. In the `evaluator_alignment.py` file, key performance indicators (KPIs) such as Cohen's kappa are calculated, and confusion matrices are displayed. These metrics help in developing an evaluator that closely matches human assessments.

## Prompt Engineering Evaluator

The evaluator returns results based on the question-answer pair, context, and the provided prompt. To align the evaluator effectively, guidelines and examples are specified to illustrate how to rate answers. Human-annotated data is then used to iteratively refine the prompt, ensuring that the evaluator's performance closely matches that of a human reviewer.

### Cohen's Kappa

Cohen's Kappa is a statistical measure used to evaluate the level of agreement between two raters or evaluators. Unlike simple percent agreement calculations, Cohen's Kappa takes into account the possibility of the agreement occurring by chance. The value of Cohen's Kappa ranges from -1 to 1, where 1 indicates perfect agreement, 0 indicates no agreement beyond chance, and negative values indicate agreement less than chance. This metric is particularly useful in scenarios where subjective judgments are made, ensuring that the evaluations are consistent and reliable.

**Interpreting Cohen’s Kappa:**
- κ < 0.20: Poor agreement
- κ = 0.21−0.39: Fair agreement
- κ = 0.40−0.59: Moderate agreement
- κ = 0.60−0.79: Substantial agreement
- κ ≥ 0.80: Almost perfect agreement

### Confusion Matrix

The script generates a confusion matrix, which is a valuable tool for evaluating the performance of the evaluator. It helps in identifying areas for improvement and understanding performance across different classes, especially in imbalanced datasets. The confusion matrix also allows you to see the trade-offs between precision, recall, and accuracy, offering a comprehensive view of the evaluator's performance.

![Evaluator Alignment](../media/img/alignment_evaluator_example.png)

## Executing Alignment

This guide explains how to execute the script for aligning the evaluator. Instructions for running the evaluator itself can be found in the [Run Evals](../run_evals/README.md) module.

### Adding Data

Add annotated data to the `custom_evals/data/input_data` folder. The default column names required are `question`, `answer`, `context`, and `human_label`. Feel free to use different column names, but note that this will require some code changes.

### Run
It is recommended to run the script from the debugger. A launch file has been provided with default launch configurations named 'Run Evaluator Alignment'.

