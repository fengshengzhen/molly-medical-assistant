import sqlite3
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


def get_session_messages(session_id: int = None):
    messages = []
    session_id = session_id or st.session_state.session_id
    session = st.session_state.robot.session_data.get(session_id)
    if not session:
        return messages

    for message in session.messages:
        if isinstance(message, SystemMessage):
            continue
        if isinstance(message, HumanMessage):
            messages.append(("user", message.content))
        elif isinstance(message, AIMessage):
            messages.append(("assistant", message.content))
    return messages


def get_all_session_ids():
    return list(st.session_state.robot.session_data.keys())


def create_response(question, session_id: int = None):
    session_id = session_id or st.session_state.session_id
    response = st.session_state.robot.stream(question, session_id)
    for chunk in response:
        yield chunk.content


def start_session():
    new_id = max(st.session_state.robot.session_data.keys(), default=0) + 1
    st.session_state.session_id = new_id
    st.session_state.robot.get_session(new_id)


def continue_session(session_id):
    st.session_state.session_id = session_id


def delete_session(session_id):
    if session_id in st.session_state.robot.session_data:
        session = st.session_state.robot.session_data.pop(session_id)
        session.clear()

        with sqlite3.connect("wkb/chat_history.db") as conn:
            conn.execute("DELETE FROM message_store WHERE session_id = ?", (str(session_id),))
            conn.commit()

        if st.session_state.robot.session_data:
            st.session_state.session_id = max(st.session_state.robot.session_data.keys())
        else:
            st.session_state.session_id = 1
            st.session_state.robot.get_session(1)