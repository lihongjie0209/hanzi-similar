import os
from typing import List, Dict

import chromadb
import numpy as np
from tqdm import tqdm


class ChromaVectorDB:
    """使用ChromaDB作为向量数据库"""

    def __init__(
        self,
        db_path: str = "./chroma_db",
        collection_name: str = "hanzi_images",
        allow_memory_fallback: bool = True,
    ):
        """初始化ChromaDB客户端，确保路径存在且可写，必要时回退到内存模式。"""
        self.collection_name = collection_name
        self.db_path = os.path.abspath(db_path)

        # 确保目录存在并可写
        os.makedirs(self.db_path, exist_ok=True)
        try:
            test_file = os.path.join(self.db_path, ".write_test")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
        except Exception as e:
            msg = f"持久化目录不可写: {self.db_path} ({e})"
            if not allow_memory_fallback:
                raise RuntimeError(msg)
            print(f"警告: {msg}，回退为内存数据库。")
            self.client = chromadb.EphemeralClient()
            self._ensure_collection()
            return

        # 尝试持久化客户端
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
        except Exception as e:
            msg = f"无法打开持久化数据库: {self.db_path} ({e})"
            if not allow_memory_fallback:
                raise RuntimeError(msg)
            print(f"警告: {msg}，回退为内存数据库。")
            self.client = chromadb.EphemeralClient()
            self._ensure_collection()
            return

        self._ensure_collection()

    def _ensure_collection(self):
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"已加载现有集合: {self.collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )
            print(f"创建新集合: {self.collection_name}")

    def add_images(self, image_paths: List[str], vectors: List[np.ndarray], metadatas: List[Dict]):
        """批量添加图像向量到数据库"""
        ids = [os.path.basename(path).replace(".png", "") for path in image_paths]

        # 转换向量为列表格式
        vectors_list = [vector.tolist() for vector in vectors]

        # 批量插入
        batch_size = 1000
        for i in tqdm(range(0, len(ids), batch_size), desc="插入向量数据库"):
            end_idx = min(i + batch_size, len(ids))
            self.collection.add(
                embeddings=vectors_list[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx],
            )

    def search_similar(self, query_vector: np.ndarray, top_k: int = 10):
        """搜索相似图像"""
        results = self.collection.query(
            query_embeddings=[query_vector.tolist()], n_results=top_k
        )

        similar_images = []
        for i in range(len(results["ids"][0])):
            similar_images.append(
                {
                    "id": results["ids"][0][i],
                    "distance": results["distances"][0][i],
                    "metadata": results["metadatas"][0][i],
                }
            )

        return similar_images

    def get_stats(self):
        """获取数据库统计信息"""
        count = self.collection.count()
        return {"total_images": count}
