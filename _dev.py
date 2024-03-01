#!/Users/donyin/miniconda3/envs/flashcard/bin/python

import json
from pathlib import Path
import streamlit as st
from src.api.bot import ChatBot
from src.prompts import GUIDE_MESSAGE_SLIDES
from natsort import natsorted
from pdf_parser import PDFParser
from streamlit_shortcuts import add_keyboard_shortcuts
from src.slides.find_similar_slide import SlidesEmbeddingHandler
from _local_variables import options_courses

# -------- [ init ] --------
st.set_page_config(layout="wide")
bot_text = ChatBot(model="gpt-4", bot_name="slide_text", system_message=GUIDE_MESSAGE_SLIDES)
bot_image = ChatBot(model="gpt-4-vision-preview", bot_name="slide_image", system_message=GUIDE_MESSAGE_SLIDES)


def dump_session_state():
    fields = [item for item in st.session_state if item.startswith("current_") and item != "current_image"]
    session_state = {}
    for field in fields:
        if isinstance(st.session_state[field], Path):
            session_state.update({field: str(st.session_state[field])})
        else:
            session_state.update({field: st.session_state[field]})
    with open("cache/session_state.json", "w") as f:
        json.dump(session_state, f, indent=4)


# -------- [load session state] --------
if Path("cache/session_state.json").exists():
    initial_session_state = json.load(open("cache/session_state.json", "r"))
    for field in initial_session_state.keys():
        if "path" in field:
            initial_session_state[field] = Path(initial_session_state[field])
        else:
            initial_session_state[field] = initial_session_state[field]
    st.session_state.update(initial_session_state)

else:
    if "current_name_course" not in st.session_state:
        st.session_state.current_name_course = list(options_courses.keys())[0]

    if "current_file_name_options" not in st.session_state:
        st.session_state.current_file_name_options = [
            file.name for file in options_courses[st.session_state.current_name_course].glob("*.pdf")
        ]
        st.session_state.current_file_name_options = natsorted(st.session_state.current_file_name_options)

    if "current_name_file" not in st.session_state:
        st.session_state.current_name_file = st.session_state.current_file_name_options[0]

    if "current_page" not in st.session_state:
        st.session_state.current_page = 0

    if "current_path_course" not in st.session_state:
        st.session_state.current_path_course = options_courses[st.session_state.current_name_course]

    if "current_path_file" not in st.session_state:
        st.session_state.current_path_file = st.session_state.current_path_course / st.session_state.current_name_file


# -------- [ init secondary ] --------
if "current_image" not in st.session_state:
    parser = PDFParser()
    parser.update_file(st.session_state.current_path_file)
    st.session_state.current_image = parser.get_page_image(st.session_state.current_page)

if "total_pages" not in st.session_state:
    parser = PDFParser()
    parser.update_file(st.session_state.current_path_file)
    st.session_state["total_pages"] = parser.doc.page_count - 1

if "slides_embedding_handler" not in st.session_state:
    st.session_state.slides_embedding_handler = SlidesEmbeddingHandler(st.session_state.current_path_course)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# -------- [callbacks] --------
def on_change_course():
    new_name_course = st.session_state["current_name_course"]
    st.session_state["current_file_name_options"] = [file.name for file in options_courses[new_name_course].glob("*.pdf")]
    st.session_state["current_file_name_options"] = natsorted(st.session_state["current_file_name_options"])
    st.session_state["current_name_file"] = st.session_state["current_file_name_options"][0]
    st.session_state["current_page"] = 0
    st.session_state["current_path_course"] = options_courses[new_name_course]
    st.session_state["current_path_file"] = st.session_state["current_path_course"] / st.session_state["current_name_file"]
    parser = PDFParser()
    parser.update_file(st.session_state["current_path_file"])
    st.session_state["current_image"] = parser.get_page_image(st.session_state["current_page"])
    st.session_state["total_pages"] = parser.doc.page_count - 1
    st.session_state["slides_embedding_handler"] = SlidesEmbeddingHandler(st.session_state["current_path_course"])

    dump_session_state()


def on_change_pdf():
    new_name_file = st.session_state["current_name_file"]
    st.session_state["current_page"] = 0
    st.session_state["current_path_file"] = st.session_state["current_path_course"] / new_name_file
    parser = PDFParser()
    parser.update_file(st.session_state["current_path_file"])
    st.session_state["current_image"] = parser.get_page_image(st.session_state["current_page"])
    st.session_state["total_pages"] = parser.doc.page_count - 1
    st.session_state["slides_embedding_handler"] = SlidesEmbeddingHandler(st.session_state["current_path_course"])

    dump_session_state()


def on_change_page():
    parser = PDFParser()
    parser.update_file(st.session_state.current_path_file)
    st.session_state.current_image = parser.get_page_image(st.session_state.current_page)

    dump_session_state()


def on_previous():
    st.session_state["current_page"] = max(st.session_state["current_page"] - 1, 0)
    on_change_page()


def on_next():
    st.session_state["current_page"] = min(st.session_state["current_page"] + 1, st.session_state["total_pages"])
    on_change_page()


with st.sidebar:
    # -------- [course and pdf selector] --------
    st.selectbox(
        "Course",
        options=options_courses.keys(),
        on_change=on_change_course,
        label_visibility="hidden",
        key="current_name_course",
    )
    st.selectbox(
        "File",
        options=st.session_state.current_file_name_options,
        on_change=on_change_pdf,
        label_visibility="hidden",
        key="current_name_file",
    )

    # -------- [page slider] --------
    st.slider(
        "Page",
        min_value=0,
        max_value=st.session_state["total_pages"],
        on_change=on_change_page,
        label_visibility="hidden",
        key="current_page",
    )

    st.button("Previous", key=None, help=None, on_click=on_previous, type="secondary", use_container_width=True)
    st.button("Next", key=None, help=None, on_click=on_next, type="secondary", use_container_width=True)

    add_keyboard_shortcuts({"-": "Previous", "=": "Next"})

    # -------- [options] --------
    st.toggle("Keep History", value=False, key=None, help=None, on_change=None, label_visibility="visible", disabled=True)
    st.toggle("Use Text", value=False, key=None, help=None, on_change=None, label_visibility="visible", disabled=True)
    st.toggle(
        "Find Related",
        value=False,
        key="mode_find_related",
        help=None,
        on_change=None,
        label_visibility="visible",
        disabled=False,
    )


# -------- [main] --------
col1, col2 = st.columns(2)

with col2:
    if "current_image" in st.session_state:
        st.image(st.session_state["current_image"])
    else:
        parser = PDFParser()
        parser.update_file(st.session_state.current_path_file)
        st.session_state.current_image = parser.get_page_image(st.session_state.current_page)
        st.image(st.session_state.current_image)


with col1:
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    with sub_col1:
        st.button("Make QA", key=None, help=None, on_click=None, type="secondary", use_container_width=True, disabled=True)
    with sub_col2:
        st.button("Find Similar", key=None, help=None, on_click=None, type="secondary", use_container_width=True, disabled=True)
    with sub_col3:
        st.button("Swtich", key=None, help=None, on_click=None, type="secondary", use_container_width=True, disabled=True)


# -------- [chat section] --------
prompt = st.chat_input("")

if prompt:
    # -------- [find similar mode] --------
    if st.session_state["mode_find_related"]:
        with col1:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                course = st.session_state["course"]
                similar_slides = st.session_state.slides_embedding_handler.get_most_similar_slides(prompt, 5)
                st.markdown("Here are the most related slides to your query:")
                for idx, (file, page) in enumerate(similar_slides):
                    st.markdown(f"{file.name} page {page}")

    # -------- [chat mode] --------
    else:
        with col1:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                # gpt_ready_image = st.session_state.pdf_parser.get_gpt_ready_page_image(st.session_state["page"])
                parser = PDFParser()
                parser.update_file(st.session_state.current_path_file)
                gpt_ready_image = parser.get_gpt_ready_page_image(st.session_state.current_page)
                response = bot_image.send(prompt, gpt_ready_image)
                bot_image._clear_chat_history()

                full_response = ""
                for token in response:
                    full_response += token.choices[0].delta.content or ""
                    message_placeholder.markdown(full_response + "▌")

                message_placeholder.markdown(full_response)


if __name__ == "__main__":
    pass
