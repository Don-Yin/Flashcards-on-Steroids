#!/Users/donyin/miniconda3/envs/flashcard/bin/python
import os
import sys
import json
from pathlib import Path
from openai import OpenAI

# from src.utils import stripe_each_line


def stripe_each_line(str):
    lines = str.split("\n")
    striped_lines = [line.strip() for line in lines]
    striped_lines = [line if line else "\n" for line in striped_lines]
    return "\n".join(striped_lines)


path_data = Path("cache", "chat_histories")
path_data.mkdir(exist_ok=True, parents=True)
client = OpenAI(api_key=os.environ.get("OPENAI_EXPERIMENTAL"))


def c_paste(text, color):
    if color == "red":
        return f"\033[31m{text}\033[0m"
    elif color == "green":
        return f"\033[32m{text}\033[0m"
    elif color == "yellow":
        return f"\033[33m{text}\033[0m"
    elif color == "blue":
        return f"\033[34m{text}\033[0m"
    elif color == "magenta":
        return f"\033[35m{text}\033[0m"
    elif color == "cyan":
        return f"\033[36m{text}\033[0m"
    elif color == "white":
        return f"\033[37m{text}\033[0m"


class ChatBot:
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        bot_name: str = "default",
        temperature: float = 0.5,
        system_message: str = "",
    ):
        self.model = model
        self.bot_name = bot_name
        self.temperature = temperature
        self.system_message = system_message
        self.history_path = path_data / (bot_name + ".json")
        self._init_chat_history()
        self._add_system_message(system_message)

    # -------- [main message function] --------
    def send(self, message, base64_image=None):
        self.add_user_message(message, base64_image)

        response = client.chat.completions.create(
            model=self.model,
            messages=self.chat_history,  # The chat history to use as context
            max_tokens=3072,  # The maximum number of tokens (words or subwords) in the generated response
            stop="[/]",  # The stopping sequence for the generated response, if any (not used here)
            temperature=self.temperature,
            stream=True,  # Whether to stream the response as it is generated
        )

        # cache = ""
        # for part in response:
        #     data = part.choices[0].delta.content or ""
        #     cache += data
        #     sys.stdout.write(c_paste(data, "green"))
        #     sys.stdout.flush()
        # print()  # newline

        # self.add_bot_response(cache)
        # self._dump_chat_history()
        return response

    # -------- [history management] --------
    def _init_chat_history(self):
        if not self.history_path.exists():
            with open(self.history_path, "w") as write_file:
                json.dump([], write_file)

        with open(self.history_path, "r") as read_file:
            self.chat_history = json.load(read_file)

    def _dump_chat_history(self):
        with open(self.history_path, "w") as write_file:
            json.dump(self.chat_history, write_file)

    def _clear_chat_history(self):
        self.chat_history = [{"role": "system", "content": self.system_message}]
        os.remove(self.history_path)

    # -------- [message management] --------
    def _add_system_message(self, message):
        """The initial introduction message"""
        message = stripe_each_line(message)
        if not self.chat_history:
            self.chat_history.append({"role": "system", "content": message})

    def add_user_message(self, message, base64_image):
        if base64_image:
            content = {
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ],
            }
        else:
            content = {"role": "user", "content": message}
        self.chat_history.append(content)

    def add_bot_response(self, message):
        self.chat_history.append({"role": "assistant", "content": message})


if __name__ == "__main__":
    bot = ChatBot(model="gpt-3.5-turbo", bot_name="default", temperature=0.5, system_message="")
    bot.send("How is a blackhole formed?")
    bot._clear_chat_history()
