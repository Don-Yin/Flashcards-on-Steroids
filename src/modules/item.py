from rich.console import Console
from rich.table import Table
from PIL import Image
from src.prompts import get_item_str


class QuizItem:
    def __init__(self, idx: int, item: dict, parent_dataset=None):
        assert "question" in item.keys(), f"Question key is required from item {item}"
        assert "answer" in item.keys(), f"Answer key is required from item {item}"
        [setattr(self, key, value) for key, value in item.items()]
        self.idx, self.correct, self.parent_dataset = idx, None, parent_dataset

        # -------- [setup the llm interaction] --------
        options = self.options if hasattr(self, "options") else ""
        image = self.image if hasattr(self, "image") else ""
        self.content_initial_prompt = get_item_str(question=self.question, options=options, answer=self.answer, image=image)

        # -------- [ additional variables ] --------
        self.item_dict = self.parent_dataset.data[self.idx]

    def present(self):
        # -------- [init table] --------
        console = Console()
        table = Table(title=f"Question {self.idx} / {len(self.parent_dataset)}")
        table.add_column("Question", style="cyan")

        # -------- [handle question to table] --------
        table.add_row(self.question)

        # -------- [handle options to table] --------
        if hasattr(self, "options"):
            table.add_column("Options", style="magenta")
            for option in self.options:
                table.add_row("", option)

        # -------- [display] --------
        console.print(table)

        # -------- [if there is an image] --------
        if hasattr(self, "image"):
            img = Image.open(self.image)
            img.show()

        # -------- [prompt user] --------
        initial_response = input("Your response: ")
        while not initial_response:
            initial_response = input("Please answer or ask a question: ")

        # -------- [init chat] --------
        self.parent_dataset.parent_session.chatbot.add_bot_response(self.content_initial_prompt)
        model_response = self.parent_dataset.parent_session.chatbot.send(initial_response)

        while "<correct>" not in model_response and "<incorrect>" not in model_response:
            user_response = input("Your response: ")
            model_response = self.parent_dataset.parent_session.chatbot.send(user_response)

        if "<correct>" in model_response:
            self.correct = True

        if "<incorrect>" in model_response:
            self.correct = False

        # -------- [followup questions] --------
        while "<end_chat>" not in model_response:
            user_response = input("Your response: ")
            model_response = self.parent_dataset.parent_session.chatbot.send(user_response)

        self.parent_dataset.parent_session.chatbot._clear_chat_history()

        return self.correct
