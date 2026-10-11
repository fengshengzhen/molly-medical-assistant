import os
import sqlite3
from typing import Iterator

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableLambda,
    RunnableWithMessageHistory,
)
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories.sql import SQLChatMessageHistory


def format_docs(docs):
    if not docs:
        return ""
    return "\n\n".join(doc.page_content for doc in docs)


class Robot:
    system_prompt = """你是“Molly医疗精灵”，一个严谨、友善的医疗导诊助手。
请严格根据“参考资料”和“本地知识库”回答，不要编造。
如果资料不足，请明确说“信息不足，建议咨询专业医生”，不要自行发挥。
回答时称呼用户为“您”，先简要分析问题，再给出建议，并注明参考来源。"""

    def __init__(self, model_config, retriever=None, db_path="wkb/chat_history.db"):
        self.retriever = retriever
        self.db_path = db_path
        self.model = ChatOpenAI(**model_config)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "用户问题：{input}\n\n参考资料：\n{rag_results}\n\n请根据以上资料回答。"),
        ])

        self.answer_chain = (
            RunnablePassthrough.assign(
                rag_results=lambda x: format_docs(self.retriever.invoke(x["input"]))
                if self.retriever else ""
            )
            | self.prompt
            | self.model
        )

        self.chain_with_history = RunnableWithMessageHistory(
            self.answer_chain,
            get_session_history=self.get_session,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

        self.load_session_data()

    def get_session(self, session_id: int) -> BaseChatMessageHistory:
        if session_id not in self.session_data:
            self.session_data[session_id] = SQLChatMessageHistory(
                session_id=session_id,
                connection=f"sqlite:///{self.db_path}",
            )
            self.session_data[session_id].add_message(SystemMessage(self.system_prompt))
        return self.session_data[session_id]

    def load_session_data(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as client:
            cur = client.cursor()
            cur.execute(
                "select count(*) from sqlite_master where type='table' and name='message_store'"
            )
            if cur.fetchall()[0][0] == 0:
                self.session_data = {}
            else:
                cur.execute("SELECT DISTINCT session_id FROM message_store")
                session_ids = cur.fetchall()
                self.session_data = {
                    int(sid[0]): SQLChatMessageHistory(
                        session_id=int(sid[0]),
                        connection=f"sqlite:///{self.db_path}",
                    )
                    for sid in session_ids
                }

    def stream(self, input_text: str, session_id: int):
        config = {"configurable": {"session_id": session_id}}
        return self.chain_with_history.stream({"input": input_text}, config=config)

    def chat(self, input_text: str, session_id: int) -> str:
        config = {"configurable": {"session_id": session_id}}
        response = self.chain_with_history.invoke({"input": input_text}, config=config)
        return response.content