#!/Users/donyin/miniconda3/envs/flashcard/bin/python

import streamlit as st
from src.api.bot import ChatBot
from src.prompts import GUIDE_MESSAGE_SLIDES
from natsort import natsorted
from pdf_parser import PDFParser
from streamlit_shortcuts import add_keyboard_shortcuts
from src.slides.find_similar_slide import SlidesEmbeddingHandler
from _local_variables import options_courses

st.set_page_config(layout="wide")
bot_text = ChatBot(model="gpt-4", bot_name="slide_text", system_message=GUIDE_MESSAGE_SLIDES)
bot_image = ChatBot(model="gpt-4-vision-preview", bot_name="slide_image", system_message=GUIDE_MESSAGE_SLIDES)


# -------- [session state] --------
if "pdf_parser" not in st.session_state:
    st.session_state["pdf_parser"] = PDFParser()

if "page" not in st.session_state:
    st.session_state.page = 0

if "total_pages" not in st.session_state:
    first_file = list(options_courses.values())[0] / list(list(options_courses.values())[0].glob("*.pdf"))[0]
    st.session_state.pdf_parser.update_file(first_file)
    st.session_state["total_pages"] = st.session_state.pdf_parser.doc.page_count - 1

if "options_pdf" not in st.session_state:
    first_course = list(options_courses.keys())[0]
    options_pdf = [pdf.name for pdf in options_courses[first_course].glob("*.pdf")]
    st.session_state["options_pdf"] = natsorted(options_pdf)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "slides_embedding_handler" not in st.session_state:
    st.session_state.slides_embedding_handler = SlidesEmbeddingHandler(options_courses["Neuroscience"])

# -------- [functions] --------
pass


# -------- [callbacks] --------
def on_change_course():
    selected_course = st.session_state["course"]
    options_pdf = [pdf.name for pdf in options_courses[selected_course].glob("*.pdf")]
    options_pdf = natsorted(options_pdf)
    st.session_state["options_pdf"] = options_pdf

    st.session_state.pdf_parser.update_file(options_courses[selected_course] / options_pdf[0])
    st.session_state.slides_embedding_handler = SlidesEmbeddingHandler(options_courses[selected_course])
    on_change_pdf()


def on_change_pdf():
    selected_pdf = st.session_state["pdf"]
    st.session_state.pdf_parser.update_file(options_courses[st.session_state["course"]] / selected_pdf)
    image_data = st.session_state.pdf_parser.get_page_image(0)
    st.session_state["current_image"] = image_data

    # Update the total number of pages in the state
    st.session_state["total_pages"] = st.session_state.pdf_parser.doc.page_count - 1
    st.session_state["page"] = 0


def on_change_page():
    page_number = st.session_state["page"]
    image_data = st.session_state.pdf_parser.get_page_image(page_number)
    st.session_state["current_image"] = image_data


def on_previous():
    st.session_state["page"] = max(st.session_state["page"] - 1, 0)
    on_change_page()


def on_next():
    st.session_state["page"] = min(st.session_state["page"] + 1, st.session_state["total_pages"])
    on_change_page()


with st.sidebar:
    # -------- [course and pdf selector] --------
    st.selectbox("Course", options=options_courses.keys(), on_change=on_change_course, label_visibility="hidden", key="course")
    st.selectbox("PDF", options=st.session_state["options_pdf"], on_change=on_change_pdf, label_visibility="hidden", key="pdf")

    # -------- [page slider] --------
    st.slider(
        "Page",
        min_value=0,
        max_value=st.session_state.pdf_parser.doc.page_count - 1,
        key="page",
        on_change=on_change_page,
        label_visibility="hidden",
    )

    st.button("Previous", key=None, help=None, on_click=on_previous, type="secondary", use_container_width=True)
    st.button("Next", key=None, help=None, on_click=on_next, type="secondary", use_container_width=True)

    add_keyboard_shortcuts(
        {
            "-": "Previous",
            "=": "Next",
        }
    )

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
        st.session_state["current_image"] = st.session_state.pdf_parser.get_page_image(0)
        st.image(st.session_state["current_image"])


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
                gpt_ready_image = st.session_state.pdf_parser.get_gpt_ready_page_image(st.session_state["page"])
                response = bot_image.send(prompt, gpt_ready_image)
                bot_image._clear_chat_history()

                full_response = ""
                for token in response:
                    full_response += token.choices[0].delta.content or ""
                    message_placeholder.markdown(full_response + "▌")

                message_placeholder.markdown(full_response)


if __name__ == "__main__":
    pass
