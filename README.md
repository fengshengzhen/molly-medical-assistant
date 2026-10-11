# Molly 医疗精灵 (Molly Medical Assistant)

基于 RAG（检索增强生成）的智能医疗导诊助手。

## ✨ 功能特性
- **本地知识库**：挂载《急性缺血性脑卒中急诊急救中国专家共识》PDF，精准回答医疗问题。
- **防幻觉设计**：基于 ChromaDB 向量检索，回答中自动标注“参考资料”，拒绝随意编造。
- **多轮对话记忆**：使用 SQLite 持久化聊天记录，支持多会话切换与历史回溯。
- **流式输出**：基于 FastAPI/Streamlit 实现流式输出，等待时有“正在检索医学知识库”的交互反馈。

## 🚀 运行步骤
## 💻 本地怎么跑起来？

1. 克隆代码到本地：
   `git clone https://github.com/fengshengzhen/molly-medical-assistant.git`
2. 安装依赖（强烈建议用 Python 3.11，新版本容易出兼容坑）：
   `pip install -r requirements.txt`
3. 配置 API Key：
   - 在根目录建一个 `.env` 文件。
   - 把 `QWEN_API_KEY=你的通义千问Key` 填进去（用 DeepSeek 就填 `OPENAI_API_KEY`）。
4. 启动项目：
   `streamlit run main.py`
## 📷 运行截图
<p align="center">
  <img src="https://github.com/user-attachments/assets/faac2d1d-89b0-4f4b-beef-15bc9ea0b799" width="48%" />
  <img src="https://github.com/user-attachments/assets/ede33604-093c-4a5d-b021-a73a1cd9cf0d" width="48%" />
</p>

## 📝 个人备注
- 踩了个坑：Qwen 的 Embedding 接口不支持 token 列表，频繁报 400 错误。后来加上 `check_embedding_ctx_length=False` 强制传纯文本才搞定。
- 目前已实现基于 RAG 的精准医疗检索，能准确区分缺血/出血性脑卒中的禁忌症，后续有空还会继续迭代。
