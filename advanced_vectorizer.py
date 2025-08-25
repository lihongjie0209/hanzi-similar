import os
import cv2
import numpy as np
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel, ViTImageProcessor, ViTModel
from typing import List, Dict, Tuple
import glob
from tqdm import tqdm
from vector_db import ChromaVectorDB

class ImageVectorizer:
    """使用预训练的视觉模型进行图像向量化"""
    
    def __init__(self, model_name="google/vit-base-patch16-224"):
        """
        初始化图像向量化器
        支持的模型:
        - "google/vit-base-patch16-224" (Vision Transformer)
        - "openai/clip-vit-base-patch32" (CLIP)
        """
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"使用设备: {self.device}")
        print(f"加载模型: {model_name}")
        
        if "clip" in model_name.lower():
            self.model = CLIPModel.from_pretrained(model_name).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(model_name)
            self.model_type = "clip"
        else:
            self.model = ViTModel.from_pretrained(model_name).to(self.device)
            self.processor = ViTImageProcessor.from_pretrained(model_name)
            self.model_type = "vit"
        
        self.model.eval()
    
    def preprocess_image(self, image_path: str) -> torch.Tensor:
        """预处理图像"""
        # 加载图像
        image = Image.open(image_path).convert('RGB')
        
        # 使用模型的processor处理图像
        if self.model_type == "clip":
            inputs = self.processor(images=image, return_tensors="pt")
            return inputs['pixel_values'].to(self.device)
        else:
            inputs = self.processor(images=image, return_tensors="pt")
            return inputs['pixel_values'].to(self.device)
    
    def extract_features(self, image_path: str) -> np.ndarray:
        """提取图像特征向量"""
        with torch.no_grad():
            pixel_values = self.preprocess_image(image_path)
            
            if self.model_type == "clip":
                # 使用CLIP的图像编码器
                image_features = self.model.get_image_features(pixel_values)
            else:
                # 使用ViT
                outputs = self.model(pixel_values)
                image_features = outputs.last_hidden_state.mean(dim=1)  # 全局平均池化
            
            # 归一化特征向量
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten()


def build_advanced_vector_database(images_dir: str = "images", 
                                   model_name: str = "google/vit-base-patch16-224"):
    """构建高级向量数据库"""
    print("=== 构建高级汉字图像向量数据库 ===")
    
    # 初始化组件
    vectorizer = ImageVectorizer(model_name)
    vector_db = ChromaVectorDB()
    
    # 获取所有图像文件
    image_paths = glob.glob(os.path.join(images_dir, "*.png"))
    print(f"找到 {len(image_paths)} 张图片")
    
    # 检查是否已有数据
    stats = vector_db.get_stats()
    if stats["total_images"] > 0:
        print(f"数据库中已有 {stats['total_images']} 条记录")
        choice = input("是否重新构建数据库？(y/N): ").lower()
        if choice != 'y':
            return vector_db, vectorizer
        
        # 清空现有数据
        vector_db.client.delete_collection(vector_db.collection_name)
        vector_db.collection = vector_db.client.create_collection(
            name=vector_db.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    # 批量处理图像
    batch_size = 100
    for i in tqdm(range(0, len(image_paths), batch_size), desc="处理图像批次"):
        batch_paths = image_paths[i:i + batch_size]
        batch_vectors = []
        batch_metadatas = []
        
        for image_path in tqdm(batch_paths, desc=f"批次 {i//batch_size + 1}", leave=False):
            try:
                # 提取特征向量
                vector = vectorizer.extract_features(image_path)
                batch_vectors.append(vector)
                
                # 准备元数据
                unicode_code = os.path.basename(image_path).replace('.png', '')
                try:
                    character = chr(int(unicode_code, 16))
                except:
                    character = "?"
                
                metadata = {
                    "unicode_code": unicode_code,
                    "character": character,
                    "image_path": image_path
                }
                batch_metadatas.append(metadata)
                
            except Exception as e:
                print(f"处理图片 {image_path} 时出错: {e}")
                continue
        
        # 批量插入数据库
        if batch_vectors:
            vector_db.add_images(batch_paths[:len(batch_vectors)], batch_vectors, batch_metadatas)
    
    print(f"向量数据库构建完成！共处理 {vector_db.get_stats()['total_images']} 张图片")
    return vector_db, vectorizer

def search_similar_characters(query_char: str, 
                            vector_db: ChromaVectorDB, 
                            vectorizer: ImageVectorizer, 
                            top_k: int = 10):
    """搜索相似字符"""
    # 获取查询字符的图片路径
    unicode_code = f"{ord(query_char):04X}"
    query_image_path = f"images/{unicode_code}.png"
    
    if not os.path.exists(query_image_path):
        print(f"字符 '{query_char}' 对应的图片 {query_image_path} 不存在")
        return []
    
    print(f"搜索与 '{query_char}' (U+{unicode_code}) 相似的字符...")
    
    # 提取查询图像的特征向量
    query_vector = vectorizer.extract_features(query_image_path)
    
    # 搜索相似图像
    results = vector_db.search_similar(query_vector, top_k)
    
    # 显示结果
    print("相似字符:")
    for i, result in enumerate(results):
        print(f"{i+1:2d}. {result['metadata']['unicode_code']} "
              f"(字符: {result['metadata']['character']}) "
              f"- 相似度: {1-result['distance']:.4f}")
    
    return results

if __name__ == "__main__":
    # 构建高级向量数据库
    vector_db, vectorizer = build_advanced_vector_database()
    
    # 测试搜索
    test_chars = ['行', '二', '人']
    for char in test_chars:
        print(f"\n{'='*50}")
        search_similar_characters(char, vector_db, vectorizer, top_k=8)
        print()
