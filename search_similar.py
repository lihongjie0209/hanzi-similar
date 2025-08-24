import os
import numpy as np
from PIL import Image
import pickle
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
import glob

def load_and_preprocess_image(image_path):
    """加载图片并预处理为向量"""
    img = Image.open(image_path).convert('L')  # 转为灰度
    img_array = np.array(img)
    # 将图片展平为一维向量
    return img_array.flatten()

def load_vector_database(save_path="vector_db.pkl"):
    """加载向量数据库"""
    with open(save_path, 'rb') as f:
        data = pickle.load(f)
    return data['pca'], data['nbrs'], data['features'], data['filenames']

def find_similar_images(query_image_path, pca, nbrs, features, filenames, top_k=5):
    """查找相似图片"""
    # 预处理查询图片
    query_feature = load_and_preprocess_image(query_image_path)
    query_feature = query_feature.reshape(1, -1)
    
    # PCA降维
    query_feature_reduced = pca.transform(query_feature)
    
    # 查找最近邻
    distances, indices = nbrs.kneighbors(query_feature_reduced, n_neighbors=top_k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            'filename': filenames[idx],
            'distance': distances[0][i],
            'unicode': filenames[idx].replace('.png', '')
        })
    
    return results

def search_similar_images(query_image_path, top_k=5):
    """搜索相似图片"""
    # 加载向量数据库
    pca, nbrs, features, filenames = load_vector_database()
    
    # 查找相似图片
    results = find_similar_images(query_image_path, pca, nbrs, features, filenames, top_k)
    
    print(f"查询图片: {query_image_path}")
    print("相似图片:")
    for i, result in enumerate(results):
        unicode_char = chr(int(result['unicode'], 16))
        print(f"{i+1}. {result['filename']} (字符: {unicode_char}) - 距离: {result['distance']:.4f}")
    
    return results

if __name__ == "__main__":
    # 示例搜索
    # 假设要搜索与某个汉字相似的图片
    query_path = "images/4E00.png"  # 一 字的unicode
    if os.path.exists(query_path):
        results = search_similar_images(query_path)
    else:
        print(f"查询图片 {query_path} 不存在，请先运行 vectorize_images.py 构建向量数据库")
