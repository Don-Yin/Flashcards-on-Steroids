#!/Users/donyin/miniconda3/envs/flashcard/bin/python

"""
This is a PDF viewer that can be used to view PDFs in a folder. It stores the current page number and the current parse mode (image vs text) in a local temp file in a fixed location of "cache/viewer_status.json".
"""

import os, json, fitz, pyautogui, pyperclip

os.environ["KIVY_NO_CONSOLELOG"] = "1"

import numpy as np
from pathlib import Path
from kivy.graphics.texture import Texture
import scipy.ndimage
from kivy.clock import Clock
from src.slides.find_similar_exam_item import DatasetEmbeddingHandler
from src.modules.dataset import FlashCardDataset
from src.api.bot import ChatBot
from src.prompts import GUIDE_MESSAGE_SLIDES_QUESTION
import base64


from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.uix.switch import Switch
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from natsort import natsorted
from kivy.uix.textinput import TextInput


class PDFViewer:
    def __init__(self, files_path: Path, dataset: FlashCardDataset, question_bot: ChatBot):
        self.dataset = dataset
        self.question_bot = question_bot
        self.files = list(files_path.glob("*.pdf"))
        self.files = natsorted(self.files, key=lambda x: x.name)
        # -------- status --------
        if Path("cache/viewer_status.json").exists():
            self._load_status()
        else:
            self.status_page, self.status_parse_mode = 0, "IMAGE"  # image vs text
            self.states_current_file = self.files[0]
            self._dump_status()

        # -------- [Initialization] --------
        self.app = App()
        self.setup_layout()

    def setup_layout(self):
        # -------- [File Setup] --------
        self.file = fitz.open(self.states_current_file)

        # -------- [Progress Bar Setup] --------
        self.progress_bar = ProgressBar(max=self._get_total_pages() - 1, size_hint=(0.8, None), height=30)
        self.page_label = Label(text=f"Page 1 / {self._get_total_pages()}", size_hint=(0.2, None), height=30)

        progress_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
        progress_layout.add_widget(self.progress_bar)
        progress_layout.add_widget(self.page_label)

        # -------- [Mode Switch Setup] --------
        self.switch = Switch(size_hint=(0.2, None), height=30)
        self.mode_label = Label(text="IMAGE", size_hint=(0.2, None), height=30)
        self.switch.bind(active=self.on_switch_move)

        top_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=100)
        top_layout.add_widget(self.mode_label)
        top_layout.add_widget(self.switch)

        # -------- [Progress Layout Integration] --------
        top_layout.add_widget(progress_layout)

        # -------- [Dropdown Setup] --------
        dropdown = DropDown()
        for pdf_file in self.files:
            dropdown_item = Button(text=pdf_file.name, size_hint_y=None, height=30)
            dropdown_item.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(dropdown_item)

        self.main_dropdown = Button(text=self.states_current_file.name, size_hint=(0.2, None), height=30)
        self.main_dropdown.bind(on_release=dropdown.open)
        dropdown.bind(on_select=self.on_dropdown_select)

        # -------- [Dropdown Integration] --------
        top_layout.add_widget(self.main_dropdown)

        # -------- [Image Widget Setup] --------
        self.image_widget = Image()

        # -------- [Buttons Setup] --------
        button_ocr = Button(text="OCR", size_hint=(0.4, 0.64))
        button_ocr.bind(on_press=self.perform_ocr)

        button_similar_item = Button(text="Find Similar Exam Item", size_hint=(0.4, 0.64))
        button_similar_item.bind(on_press=self.show_most_similar_item)

        button_make_qa = Button(text="Make QA", size_hint=(0.4, 0.64))
        button_make_qa.bind(on_press=self.make_slide_question)

        button_show_random_pdf = Button(text="Show Random PDF", size_hint=(0.4, 0.64))
        button_show_random_pdf.bind(on_press=self.show_random_pdf)

        # -------- [OCR Button Integration] --------
        ocr_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=100)
        ocr_layout.add_widget(button_show_random_pdf)
        ocr_layout.add_widget(button_ocr)
        ocr_layout.add_widget(button_similar_item)
        ocr_layout.add_widget(button_make_qa)

        # -------- [OCR text area Setup] --------
        self.ocr_results = TextInput(text="", multiline=True, size_hint_x=1, size_hint_y=None)
        Clock.schedule_interval(self.update_textinput_height, 0.5)  # Check every 0.5 seconds

        # -------- [Main Layout Setup] --------
        self.layout = BoxLayout(orientation="vertical")
        self.layout.add_widget(top_layout)
        self.layout.add_widget(self.image_widget)
        self.layout.add_widget(self.ocr_results)
        self.layout.add_widget(ocr_layout)

        # -------- [Window Setup] --------
        screen_width, screen_height = pyautogui.size()
        Window.size = (screen_width / 2, screen_height)
        Window.left = screen_width / 2
        Window.bind(on_keyboard=self.on_keyboard)

        # -------- [App Initialization] --------
        self.app.build = lambda: self.layout
        self.switch_file()
        self.switch_page()

    # ----[ callbacks ]----
    def show_random_pdf(self, instance):
        random_file = np.random.choice(self.files)
        self.main_dropdown.text = random_file.name
        self.ocr_results.text = ""
        self.status_page = 0
        self.switch_file(random_file)

    def make_slide_question(self, instance):
        """
        1. ocr the slides and find the most relavant item in the self.dataset including the answer
        2. feed(item, slide, prompt) to make a qa
        3. show the qa in the ocr_results and clipboard
        """
        items_str = self.show_most_similar_item(instance)
        page = self.file.load_page(self.status_page)
        image = page.get_pixmap()
        image = image.tobytes("png")
        image = base64.b64encode(image).decode("utf-8")
        instruction = f"""# Examples: {items_str}"""
        response = self.question_bot.send(instruction, image)
        self.question_bot._clear_chat_history()
        # self.ocr_results.text = response
        pyperclip.copy(response)

    def perform_ocr(self, instance):
        page = self.file.load_page(self.status_page)
        text = page.get_text()
        self.ocr_results.text = text

    def show_most_similar_item(self, instance):
        """ocr the slide and find the most relavant item in the self.dataset"""
        page = self.file.load_page(self.status_page)
        text = page.get_text()

        embedding_handler = DatasetEmbeddingHandler(dataset=self.dataset)
        # item = embedding_handler.find_most_similar_item(text)
        items = embedding_handler.find_most_similar_item(text)
        # item_first = items[0]
        items_dict_str = ""
        for item in items:
            items_dict_str += json.dumps(item.item_dict, indent=4) + "\n"
        # item_dict_str = json.dumps(item.item_dict, indent=4)
        # self.ocr_results.text = item_dict_str
        self.ocr_results.text = items_dict_str

        pyperclip.copy(items_dict_str)
        return items_dict_str

    def update_textinput_height(self, dt):
        lines = max(1, len(self.ocr_results._lines))
        line_height = self.ocr_results.line_height
        new_height = lines * line_height
        self.ocr_results.height = max(64, new_height)  # 64 is the minimum height

    def on_dropdown_select(self, instance, text):
        selected_file = next((f for f in self.files if f.name == text), None)
        if selected_file:
            self.main_dropdown.text = selected_file.name
            self.ocr_results.text = ""
            self.status_page = 0
            self.switch_file(selected_file)

    def on_keyboard(self, instance, key, *args):
        """
        keyboard event handler
        """
        if key == 45:  # Key code for "-"
            new_page = max(0, self.status_page - 1)  # Decrement page but don't go below 0
            self.switch_page(new_page)
            self.ocr_results.text = ""

        if key == 61:  # Key code for "="
            new_page = min(self.status_page + 1, self._get_total_pages() - 1)  # Increment page but don't go beyond total pages
            self.switch_page(new_page)
            self.ocr_results.text = ""

        return True

    def on_switch_move(self, instance, value):
        """
        The switch between image and text mode
        """
        self.status_parse_mode = "TEXT" if value else "IMAGE"
        self.mode_label.text = f"{self.status_parse_mode}"
        self.switch_page()

    # -------- [page switch related stuff] --------
    def switch_file(self, file: Path = None):
        if file:
            self.states_current_file = file
        self.file = fitz.open(self.states_current_file)
        self.progress_bar.max = self._get_total_pages() - 1
        self.switch_page(0)

    def switch_page(self, page_num: int = None):
        if page_num:
            self.status_page = page_num
        self.update_image(self.status_page)
        self.update_page_label(self.status_page)
        self._dump_status()
        # self._clear_all_chat_histories()

    def update_image(self, page_num: int, scale: float = 2):
        assert page_num in range(self._get_total_pages()), f"page_num {page_num} not in 0 - {self._get_total_pages() - 1}"
        page = self.file.load_page(page_num)

        pix = page.get_pixmap()
        img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        img_data = np.flipud(img_data)

        scaled_height, scaled_width = int(pix.height * scale), int(pix.width * scale)
        img_data = scipy.ndimage.zoom(img_data, (scale, scale, 1), order=0)
        texture = Texture.create(size=(scaled_width, scaled_height), colorfmt="rgb")
        texture.blit_buffer(img_data.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
        self.image_widget.texture = texture
        self.progress_bar.value = page_num

    def update_page_label(self, page_num):
        self.page_label.text = f"Page {page_num + 1} / {self._get_total_pages()}"

    # ----[ helper functions ]----
    def _get_total_pages(self):
        """
        Return the total number of pages in the PDF.
        """
        return self.file.page_count

    def _dump_status(self):
        """
        self.status_page, self.status_parse_mode = 0, "IMAGE"
        self.states_current_file = self.files[0]
        save in cache/viewer_status.json
        """
        status = {}
        status.update({"page": self.status_page})
        status.update({"parse_mode": self.status_parse_mode})
        status.update({"current_file": self.states_current_file.as_posix()})
        with open(Path("cache/viewer_status.json"), "w") as f:
            json.dump(status, f, indent=4)

    def _load_status(self):
        with open(Path("cache/viewer_status.json"), "r") as f:
            status = json.load(f)
            self.status_page = status["page"]
            self.status_parse_mode = status["parse_mode"]
            self.states_current_file = Path(status["current_file"])

    def _clear_all_chat_histories(self):
        for file in Path("cache/chat_histories").glob("*"):
            os.remove(file)


if __name__ == "__main__":
    bot_image_question = ChatBot(
        model="gpt-4-vision-preview", bot_name="default_image_question", system_message=GUIDE_MESSAGE_SLIDES_QUESTION
    )
    files = Path("/Users/donyin/Dropbox/~desktop/modules/neuroscience/lectures/")
    dataset = FlashCardDataset(data_path=Path("data", "neuroscience.yaml"))
    viewer = PDFViewer(files_path=files, dataset=dataset, question_bot=bot_image_question)
    viewer.app.run()
