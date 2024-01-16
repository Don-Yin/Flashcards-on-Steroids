from src.modules.item import QuizItem
from torch.utils.data import Dataset
from pathlib import Path
import yaml
import random


class FlashCardDataset(Dataset):
    def __init__(self, data_path: Path = None, data: list[dict] = None):
        assert data_path or data and not (data_path and data), "Either data_path or data must be provided (not both)."

        if data_path:
            with open(data_path) as file:
                self.data = yaml.load(file, Loader=yaml.FullLoader)
            self.check_key_types(self.data)
            self.quiz_items = [QuizItem(idx, item, self) for idx, item in enumerate(self.data)]

        if data:
            self.data = data
            self.quiz_items = [QuizItem(idx, item, self) for idx, item in enumerate(self.data)]

        # -------- [additional variables] --------
        self.data_path = data_path
        self.dataset_name = data_path.stem if data_path else "custom_dataset"

    # -------- [some dunders] --------
    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx: int):
        return self.quiz_items[idx]

    # -------- [helpers] --------
    @staticmethod
    def check_key_types(data: list[dict]):
        """check the types of keys in the data are all expected
        becuase the way each question is presented is associated with the keys
        """
        expected_keys = {"question", "options", "answer", "image"}
        presented_keys = {key for item in data for key in item.keys()}
        # assert presented_keys == expected_keys, f"Expected keys: {expected_keys}, presented keys: {presented_keys}"
        # assert presented keys is subset of expected keys
        assert presented_keys.issubset(expected_keys), f"Expected keys: {expected_keys}, presented keys: {presented_keys}"

    def train_test_split(self, train_ratio=0.8, seed=42):
        random.seed(seed)
        shuffled_items = self.data.copy()
        random.shuffle(shuffled_items)
        split_idx = int(len(shuffled_items) * train_ratio)
        train_data, test_data = shuffled_items[:split_idx], shuffled_items[split_idx:]
        return FlashCardDataset(data=train_data), FlashCardDataset(data=test_data)