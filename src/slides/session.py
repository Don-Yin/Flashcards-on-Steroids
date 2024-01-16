#!/Users/donyin/miniconda3/envs/flashcard/bin/python

"""
we need a class here
it should:
1. load cache/viewer_status.json
2. do a interactive session with user using the text / image as context
3. in a terminal, user can type in commands to do things
4. each time use swtiches to a new page, the context will be sent once in the first message
"""

import json, fitz, time
from pathlib import Path
import base64
from src.api.bot import ChatBot
from src.prompts import GUIDE_MESSAGE_SLIDES


class SlideTalk:
    def __init__(self, chatbot_text: ChatBot, chatbot_image: ChatBot):
        self.chatbot_text, self.chatbot_image = chatbot_text, chatbot_image
        self.init_main()

    def init_main(self):
        """
        keep prompting the user
        create a new chat each time the user make any input
        """
        while True:
            self._prompt_user()
            self._load_status()
            self.chat_completed = False  # Initialize a flag
            self._create_chat()
            while not self.chat_completed:  # Wait until chat is complete
                time.sleep(0.1)  # Avoid busy waiting

    # -------- [loop methods / steps] --------
    def _prompt_user(self):
        self.user_input = input(">>> ")
        while not self.user_input:
            self.user_input = input(">>> ")

    def _load_status(self):
        with open(Path("cache/viewer_status.json"), "r") as f:
            self.status = json.load(f)

    def _create_chat(self):
        """
        example_status = {
            "page": 8,
            "parse_mode": "IMAGE",
            "current_file": "/Users/donyin/Dropbox/~desktop/modules/neuroscience/lectures/1.pdf"
        }
        """
        ocr_text, image = self._load_pdf_page()
        image = image.tobytes("png")
        image = base64.b64encode(image).decode("utf-8")
        match self.status["parse_mode"]:
            case "TEXT":
                instruction = ocr_text + "\n" + self.user_input
                _ = self.chatbot_text.send(instruction, None)
                self.chatbot_text._clear_chat_history()
            case "IMAGE":
                instruction = ocr_text + "\n" + self.user_input
                _ = self.chatbot_image.send(instruction, image)
                self.chatbot_image._clear_chat_history()
            case _:
                raise ValueError(f"Parse_mode must be one of TEXT or IMAGE, got {self.status['parse_mode']}")
        self.chat_completed = True

    # -------- [helpers] --------
    def _load_pdf_page(self):
        """both as text and image"""
        file = Path(self.status["current_file"])
        file = fitz.open(file)
        page = file.load_page(self.status["page"])
        ocr_text, image = page.get_text("text"), page.get_pixmap()
        return ocr_text, image


if __name__ == "__main__":
    bot_text = ChatBot(model="gpt-4", bot_name="slide_text", system_message=GUIDE_MESSAGE_SLIDES)
    bot_image = ChatBot(model="gpt-4-vision-preview", bot_name="slide_image", system_message=GUIDE_MESSAGE_SLIDES)
    session = SlideTalk(chatbot_text=bot_text, chatbot_image=bot_image)
