import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PDFMinerLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class MyChroma(Chroma):
    embedding_function = OpenAIEmbeddings(
        model="text-embedding-v3",
        api_key=os.getenv("QWEN_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        check_embedding_ctx_length=False,
    )

    def add_files(self, filename):
        document = PDFMinerLoader(filename).load()
        splits = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=80,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        ).split_documents(document)
        self.add_documents(splits)

    @classmethod
    def from_folder(cls, persist_directory, collection_name, folder_path=None):
        self = cls(
            collection_name=collection_name,
            embedding_function=cls.embedding_function,
            persist_directory=persist_directory,
        )

        # 如果集合已有数据，就不再重复导入
        try:
            count = self._collection.count()
        except Exception:
            count = 0

        if folder_path and os.path.isdir(folder_path) and count == 0:
            files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.endswith(".pdf")
            ]
            for f in files:
                self.add_files(f)

        return self