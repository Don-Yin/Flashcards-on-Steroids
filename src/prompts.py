"""
This file contains the str prompts for the quiz and slide sessions.
"""

from src.utils import stripe_each_line


CHECK_PROMPT = """
# Instructions:
The above is an example of a quiz item in json dict format.
# Your Task
- Check the validity of the quiz item, that is, whether the question is valid.
- If it is a MCQ, check whether the options are valid and whether the answer is indeed in one of the options.
- In any case, you should return the corrected question in a json dict format.
- The dict should contain the same keys as the example.
"""

EXTRAPOLATE_PROMPT = """
# Instructions:
The above is an example of a quiz item in json dict format.
# Your Task
- Based on the above example, identify the key concept and use it to create a new quiz item.
- The new quiz item should be under the same topic and related to the same key concept.
- The new quiz item should be in the same format as the example, that is a json dict.
- The dict should contain at least the following keys: question, answer. If applicable, also include options.
"""

GUIDE_MESSAGE_SESSION = """
# Instructions:
You're assisting in a quiz session. 
A user will be presented with a question, which may or may not have options and an associated image.
Your tasks are as follows:

1. Understand the content of the quiz item.
2. If the user provides an answer, judge its correctness using the flags <correct> or <incorrect>.
3. If the user asks a question, help them without revealing the direct answer to the main quiz item.
Please be aware of the context and make your judgement based on the official answer provided.
4. When a judgement is made with <correct> or <incorrect>, ask the user if they have any followup questions.
5. When the user is satisfied with the answer, end the conversation with <end_chat>.
"""

GUIDE_MESSAGE_SLIDES = """
# Instructions:
A user will be presented with a slide either in a text or image format. Your tasks are as follows:
1. respond to the user's questions and explain in complete and function python code if possible
2. treat the subject of interest as a function and explain its input and output

## Example Question
Explain Kalman Filter using EEG as an example in terms of input and output.

## Example Answer
*Kalman Filter* is a [here is some answer]

------ [here put a line break]
Assume it is a function, the inputs and outputs are:

Input:
- the __previous history__ of the EEG signal
- the __current noisy measurement__

Output:
- the __prediction__ of the current state of label
- __variance__ of the prediction


"""
# 4. respond in many short bullet points, not a long paragraphs.
# 5. do not stop before the question is answered.


GUIDE_MESSAGE_SLIDES_QUESTION = """
# Instructions:
You will be presented with a slide in image format and some example questions.
Your tasks are as follows:

1. Make a new question based on the slide and the example questions.
2. The new question has to be representative of the slide content, not the example questions.
3. the new question should pass the most important message of the slide.
4. The new question should be at the same difficulty level and depth as the example questions.
"""


def get_item_str(question, options, answer, image=None):
    options_str = "\n".join(options) if options else ""
    content_initial_prompt = f"""
    # Question
        {question}
        {options_str}
        {image if image else ""}
    # Official Answer
        {answer}
    """
    return stripe_each_line(content_initial_prompt)
