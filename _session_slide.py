#!/Users/donyin/miniconda3/envs/flashcard/bin/python

"""
this is the main script that starts the slide session with an viewer
remember to set yabai / python manage to true / false in the ~/.config/yabai/yabairc file and do yabai --restart-service
"""

from src.prompts import GUIDE_MESSAGE_SLIDES, GUIDE_MESSAGE_SLIDES_QUESTION
import multiprocessing, os
from src.slides.session import SlideTalk
from src.api.bot import ChatBot
from pathlib import Path
from src.modules.dataset import FlashCardDataset
from src.api.bot import ChatBot
from src.slides.viewer import PDFViewer


def run_command(command):
    conda_activate = "/Users/donyin/miniconda3/bin/activate"
    conda_env = "flashcard"
    full_command = f"source {conda_activate} {conda_env} && {command}"
    os.system(f"bash -c '{full_command}'")


def main():
    session_process = multiprocessing.Process(target=run_command, args=("python -m src.slides.session",))
    viewer_process = multiprocessing.Process(target=run_command, args=("python -m src.slides.viewer",))

    session_process.start()
    viewer_process.start()

    try:
        session_process.join()

    except KeyboardInterrupt:
        print("Terminating processes...")

    finally:
        if viewer_process.is_alive():
            viewer_process.terminate()
            viewer_process.join()

        if session_process.is_alive():
            session_process.terminate()
            session_process.join()


class SlideSesson:
    def __init__(self):
        pass

    def _init_session(self):
        bot_text = ChatBot(model="gpt-4", bot_name="slide_text", system_message=GUIDE_MESSAGE_SLIDES)
        bot_image = ChatBot(model="gpt-4-vision-preview", bot_name="slide_image", system_message=GUIDE_MESSAGE_SLIDES)
        session = SlideTalk(chatbot_text=bot_text, chatbot_image=bot_image)

    def _init_viewer(self):
        bot_image_question = ChatBot(
            model="gpt-4-vision-preview", bot_name="default_image_question", system_message=GUIDE_MESSAGE_SLIDES_QUESTION
        )
        files = Path("/Users/donyin/Dropbox/~desktop/modules/neuroscience/lectures/")
        dataset = FlashCardDataset(data_path=Path("data", "neuroscience.yaml"))
        viewer = PDFViewer(files_path=files, dataset=dataset, question_bot=bot_image_question)
        viewer.app.run()


if __name__ == "__main__":
    main()
