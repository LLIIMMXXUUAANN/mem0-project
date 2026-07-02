"""Streamlit UI: multi-user chat with Mem0 memory + a memory browser panel."""
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from mem0 import MemoryClient

from gemini_service import GeminiService, GeminiServiceError
from mem0_service import Mem0Service, Mem0ServiceError

load_dotenv()

st.set_page_config(page_title="Mem0 + Gemini Assistant", page_icon=":brain:")


@st.cache_resource
def get_mem0_service() -> Mem0Service:
    return Mem0Service(MemoryClient(api_key=os.environ["MEM0_API_KEY"]))


@st.cache_resource
def get_gemini_service() -> GeminiService:
    return GeminiService(genai.Client(api_key=os.environ["GEMINI_API_KEY"]))


def check_api_keys() -> bool:
    missing = [
        name for name in ("MEM0_API_KEY", "GEMINI_API_KEY") if not os.environ.get(name)
    ]
    if missing:
        st.error(
            "Missing environment variable(s): "
            + ", ".join(missing)
            + ". Add them to your .env file (see .env.example) and restart."
        )
        return False
    return True


def render_chat(mem0_service: Mem0Service, gemini_service: GeminiService, user_id: str) -> None:
    history_key = f"chat_history:{user_id}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    if st.button("Clear chat", key="clear_chat_button"):
        st.session_state[history_key] = []

    history = st.session_state[history_key]

    for turn in history:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
            if turn["role"] == "assistant" and turn.get("memories_used"):
                with st.expander("Memories used"):
                    for fact in turn["memories_used"]:
                        st.markdown(f"- {fact}")

    user_message = st.chat_input("Say something...")
    if not user_message:
        return

    history.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    try:
        memories = mem0_service.search_memories(user_id, user_message)
    except Mem0ServiceError as exc:
        st.error(str(exc))
        return
    memory_texts = [memory.text for memory in memories]

    try:
        reply = gemini_service.generate_reply(user_message, memory_texts, history[:-1])
    except GeminiServiceError as exc:
        st.error(str(exc))
        return

    with st.chat_message("assistant"):
        st.markdown(reply)
        if memory_texts:
            with st.expander("Memories used"):
                for fact in memory_texts:
                    st.markdown(f"- {fact}")

    history.append({"role": "assistant", "content": reply, "memories_used": memory_texts})

    try:
        mem0_service.add_memory(
            user_id,
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": reply},
            ],
        )
    except Mem0ServiceError as exc:
        st.warning(f"Reply shown, but saving memory failed: {exc}")


def render_memory_browser(mem0_service: Mem0Service, user_id: str) -> None:
    st.subheader(f"Memories for {user_id}")

    query = st.text_input("Search memories", key="memory_search_query")
    search_clicked = st.button("Search", key="memory_search_button")
    show_all_clicked = st.button("Show all memories", key="memory_show_all_button")

    results = []
    if search_clicked and query:
        try:
            results = mem0_service.search_memories(user_id, query)
        except Mem0ServiceError as exc:
            st.error(str(exc))
    elif show_all_clicked:
        try:
            results = mem0_service.get_all_memories(user_id)
        except Mem0ServiceError as exc:
            st.error(str(exc))

    for memory in results:
        col1, col2 = st.columns([5, 1])
        col1.markdown(f"- {memory.text}")
        if col2.button("Delete", key=f"delete_{memory.id}"):
            try:
                mem0_service.delete_memory(memory.id)
                st.success("Deleted. Click 'Show all memories' to refresh.")
            except Mem0ServiceError as exc:
                st.error(str(exc))


def main() -> None:
    st.title("Mem0 + Gemini Personal Assistant")

    if not check_api_keys():
        st.stop()

    user_id = st.sidebar.text_input("User ID", value="alice")
    if not user_id:
        st.sidebar.warning("Enter a user ID to start chatting.")
        st.stop()

    try:
        mem0_service = get_mem0_service()
        gemini_service = get_gemini_service()
    except Exception as exc:
        st.error(f"Failed to connect to Mem0 Cloud or Gemini: {exc}")
        st.stop()

    chat_tab, memory_tab = st.tabs(["Chat", "Memory browser"])
    with chat_tab:
        render_chat(mem0_service, gemini_service, user_id)
    with memory_tab:
        render_memory_browser(mem0_service, user_id)


if __name__ == "__main__":
    main()
