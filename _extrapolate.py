#!/Users/donyin/miniconda3/envs/flashcard/bin/python

"""
dataset extrapolator

extrapolate_datasets(
    dataset=dataset,
    output_folder=Path("data", "extrapolated_neuroscience"),
    num_samples=3,
)

"""
import json, yaml, os
from pathlib import Path
from src.modules.dataset import FlashCardDataset
from src.prompts import EXTRAPOLATE_PROMPT, CHECK_PROMPT
from src.api.bot import ChatBot


class Extrapolator:
    def __init__(self, dataset: FlashCardDataset, output_folder: Path, num_samples: int, bot: ChatBot):
        self.dataset, self.output_folder = dataset, output_folder
        self.bot, self.num_samples = bot, num_samples
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def extrapolate(self):
        for i in range(self.num_samples):
            self.new_items = []
            for item in self.dataset.data:
                new_item = self.extrapolate_single_item(item)
                self.new_items.append(new_item)
            self.save(_as=f"sample_{i}")

    def save(self, _as: str):
        yaml.dump(self.new_items, open(self.output_folder / f"{_as}.yaml", "w"), indent=4)

    def extrapolate_single_item(self, item: dict):
        success = False
        formatted_item = json.dumps(item, indent=4)
        while not success:
            try:
                new_item = self.bot.send(message=formatted_item)
                new_item = new_item[new_item.find("{") : new_item.rfind("}") + 1]
                new_item = json.loads(new_item)
                success = True
            except json.decoder.JSONDecodeError:
                pass
        self.bot._clear_chat_history()
        return new_item


class DatasetChecker:
    def __init__(self, extrapolate_folder: Path, bot: ChatBot):
        """
        check both the validity and the completeness of a dataset
        """
        self.extrapolate_folder, self.bot = extrapolate_folder, bot

    def check(self):
        """the main function"""
        datasets_files = os.listdir(self.extrapolate_folder)
        for file in datasets_files:
            self.check_single_file(file)

    def check_single_file(self, name: str):
        dataset = FlashCardDataset(data_path=self.extrapolate_folder / name)
        dataset_new = []
        for item in dataset.data:
            new_item = self.check_single_item(item)
            dataset_new.append(new_item)
        yaml.dump(dataset_new, open(self.extrapolate_folder / name, "w"), indent=4)

    def check_single_item(self, item: dict):
        success = False
        formatted_item = json.dumps(item, indent=4)
        while not success:
            try:
                new_item = self.bot.send(message=formatted_item)
                new_item = new_item[new_item.find("{") : new_item.rfind("}") + 1]
                new_item = json.loads(new_item)
                success = True
            except json.decoder.JSONDecodeError:
                pass
        self.bot._clear_chat_history()
        return new_item


if __name__ == "__main__":
    # ---- variables ----
    extrapolate_path = Path("data", "extrapolated_neuroscience")

    # ---- extrapolate dataset ----
    bot = ChatBot(model="gpt-4", bot_name="default", temperature=0.5, system_message=EXTRAPOLATE_PROMPT)
    dataset = FlashCardDataset(data_path=Path("data", "neuroscience.yaml"))
    train, test = dataset.train_test_split(train_ratio=0.8, seed=42)
    extrapolator = Extrapolator(dataset=test, output_folder=extrapolate_path, num_samples=3, bot=bot)
    extrapolator.extrapolate()

    # ---- check extrapolated dataset ----
    bot = ChatBot(model="gpt-4", bot_name="default", temperature=0.5, system_message=CHECK_PROMPT)
    dataset_checker = DatasetChecker(extrapolate_folder=extrapolate_path, bot=bot)
    dataset_checker.check()
