import  random
import os
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import funcs
from robot import Robot
from chroma_store import MyChroma

# ========== 页面配置 ==========
st.set_page_config(
    page_title="Molly医疗精灵",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========== 自定义 CSS 美化 ==========
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8f0fe 100%);
    }
    .stChatMessage {
        border-radius: 16px;
        padding: 12px 16px;
        margin-bottom: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .stButton button {
        border-radius: 20px;
        border: 1px solid #1e88e5;
        color: #1e88e5;
        background-color: #ffffff;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: #1e88e5;
        color: #ffffff;
    }
    h1 {
        color: #0d47a1;
        font-weight: 700;
    }
    .sidebar .sidebar-content {
        background: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# ========== 初始化 ==========
if "started" not in st.session_state:
    st.session_state.started = True

    os.makedirs("./wkb/rag", exist_ok=True)
    os.makedirs("./wkb/docs", exist_ok=True)

    st.session_state.chroma = MyChroma.from_folder(
        persist_directory="./wkb/rag",
        collection_name="rag_collection",
        folder_path="./wkb/docs",
    )

    retriever = st.session_state.chroma.as_retriever(search_kwargs={"k": 3})

    st.session_state.robot = Robot(
        model_config={
            "model": "qwen-plus",
            "temperature": 0.1,
            "api_key": os.getenv("QWEN_API_KEY"),  # <--- 明确指定 Key
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"  # <--- 明确指定 Qwen 的地址
        },
        retriever=retriever,
        db_path="wkb/chat_history.db",
    )

    funcs.start_session()

# ========== 顶部 Logo + 标题 ==========
col1, col2 = st.columns([1, 7])
with col1:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=80)
with col2:
    st.title("Molly 医疗精灵")
    st.caption("基于 RAG 的智能医疗导诊助手 · 回答仅供参考，不能替代医生诊断")
    st.caption("📚 当前知识库来源：《急性缺血性脑卒中急诊急救中国专家共识》")

# ========== 侧边栏 ==========
with st.sidebar:
    st.header("💬 对话管理")
    st.button("➕ 开始新会话", on_click=funcs.start_session,
              use_container_width=True, key="new_session")
    st.divider()

    st.subheader("历史会话")
    session_ids = funcs.get_all_session_ids()
    if not session_ids:
        st.info("暂无历史会话")
    else:
        for session_id in sorted(session_ids, reverse=True):
            with st.expander(f"对话 #{session_id}"):
                col_a, col_b = st.columns(2)
                col_a.button("继续", on_click=funcs.continue_session,
                             args=(session_id,), key=f"continue_{session_id}",
                             use_container_width=True)
                col_b.button("删除", on_click=funcs.delete_session,
                             args=(session_id,), key=f"delete_{session_id}",
                             use_container_width=True)

                messages = funcs.get_session_messages(session_id)
                for role, content in messages[-3:]:
                    with st.chat_message(role):
                        st.write(content[:60] + "..." if len(content) > 60 else content)

    st.divider()
    st.caption("⚠️ 本助手回答基于医学知识库，仅供参考，不能替代专业医疗建议。")

# ========== 聊天记录 ==========
messages = funcs.get_session_messages()
for role, content in messages:
    avatar = "🧑" if role == "user" else "🏥"
    with st.chat_message(role, avatar=avatar):
        st.write(content)

# ========== 示例问题 ==========
if not messages:
    st.markdown("#### 你可以问我：")
    # 定义一个大一点的问题池
    all_questions = [
        "急性缺血性脑卒中的静脉溶栓时间窗是多久？",
        "如何快速识别脑卒中早期症状？",
        "脑卒中急救的黄金时间是多少？",
        "rt-PA静脉溶栓治疗的绝对禁忌症有哪些？",
        "为什么说'时间就是大脑'？",
        "2013年中国卒中的年龄标化患病率是多少？"
    ]
    # 每次刷新页面时，从问题池里随机抽 3 个展示
    examples = random.sample(all_questions, k=3)

    # 根据抽取的问题数量，动态生成列
    cols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        if cols[i].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state.preset_question = ex
            st.rerun()

# ========== 处理输入 ==========
question = st.chat_input("请输入您的医疗问题...")

# 如果点击了预设问题按钮，从 session_state 里取出来
if "preset_question" in st.session_state and st.session_state.preset_question:
    question = st.session_state.preset_question
    st.session_state.preset_question = None  # 取完立刻清空，防止重复触发！

if question:
    # 1. 显示用户问题
    with st.chat_message("user", avatar="🧑"):
        st.write(question)

    # 2. 显示 AI 思考过程和回答
    with st.chat_message("assistant", avatar="🏥"):
        with st.spinner("正在检索医学知识库..."):
            # 注意：这里的 create_response 返回的是流式生成器
            response_stream = funcs.create_response(question)
            # 使用 st.write_stream 直接流式输出，体验更好
            st.write_stream(response_stream)

    # 3. 重新运行，刷新聊天历史
    st.rerun()