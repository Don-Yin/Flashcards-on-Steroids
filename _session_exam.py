#!/Users/donyin/miniconda3/envs/flashcard/bin/python

"""
the initiate script for an exam session
"""

from pathlib import Path
from src.api.bot import ChatBot
from src.modules.session import Session
from src.modules.dataset import FlashCardDataset
from src.prompts import GUIDE_MESSAGE_SESSION


if __name__ == "__main__":
    # -------- [get stuff ready] --------
    dataset = FlashCardDataset(data_path=Path("data", "neuroscience.yaml"))
    data_train, data_test = dataset.train_test_split(train_ratio=0.8, seed=42)
    bot = ChatBot(model="gpt-4", bot_name="default", temperature=0.5, system_message=GUIDE_MESSAGE_SESSION)

    # -------- [session] --------
    # session_train = Session(chatbot=bot, dataset=data_train, session_name="stats_train")
    # session_train.start()

    # session_test = Session(chatbot=bot, dataset=data_test, session_name="stats_test")
    # session_test.start()
