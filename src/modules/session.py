import json
from rich import print
from pathlib import Path
from src.api.bot import ChatBot
from src.modules.dataset import FlashCardDataset


class Session:
    def __init__(
        self,
        chatbot: ChatBot,
        dataset: FlashCardDataset,
        session_name: str,
    ):
        self.score = None
        self.chatbot = chatbot  # do not remove, used by children
        self.dataset = dataset
        self.dataset.parent_session = self
        self.save_path = Path("cache", "sessions", f"{session_name}.json")
        self.save_path.parent.mkdir(exist_ok=True, parents=True)
        self.progress = {idx: None for idx, _ in enumerate(self.dataset)}

        if self.save_path.exists():
            self._load()

    def start(self):
        markers = [None]

        for idx, quiz_item in enumerate(self.dataset):
            if self.progress[idx] in markers:
                quiz_item.present()
                self._save()

        self._on_end()

    def _on_end(self):
        """count the score and print"""
        self.score = sum(self.progress.values()) / len(self.progress)
        print(f"Your score is {self.score}. {sum(self.progress.values())} / {len(self.progress)}")

    def _save(self):
        """
        Save the session progress to a JSON file.
        The key is the index of the quiz item (as an integer),
        and the value is the correct flag, either True or False.
        """
        # Ensure that the keys are integers
        self.progress = {int(idx): quiz_item.correct for idx, quiz_item in enumerate(self.dataset)}
        with open(self.save_path, "w") as file:
            json.dump(self.progress, file, indent=4)

    def _load(self):
        """
        Load the session from a checkpoint.
        Update the quiz correctness based on the checkpoint.
        """
        loaded_progress = json.load(open(self.save_path))
        self.progress = (
            {int(idx): correct for idx, correct in loaded_progress.items()}
            if isinstance(list(loaded_progress.keys())[0], str)
            else loaded_progress
        )
        for idx, quiz_item in enumerate(self.dataset):
            quiz_item.correct = self.progress[idx]
