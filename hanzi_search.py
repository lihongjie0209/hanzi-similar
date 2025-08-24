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

def search_by_character(character, top_k=5):
    """通过汉字字符搜索相似图片"""
    unicode_hex = f"{ord(character):04X}"
    query_path = f"images/{unicode_hex}.png"
    
    if not os.path.exists(query_path):
        print(f"字符 '{character}' 对应的图片文件 {query_path} 不存在")
        return []
    
    return search_similar_images(query_path, top_k)

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

def interactive_search():
    """交互式搜索"""
    print("汉字相似度搜索系统")
    print("输入 'q' 退出")
    
    while True:
        query = input("\n请输入要搜索的汉字: ").strip()
        if query.lower() == 'q':
            break
        
        if len(query) != 1:
            print("请输入单个汉字")
            continue
        
        try:
            results = search_by_character(query)
            if not results:
                print("未找到相似图片")
        except Exception as e:
            print(f"搜索出错: {e}")

if __name__ == "__main__":
    # 可以选择交互式搜索或直接搜索
    choice = input("选择模式: 1-交互式搜索, 2-测试搜索 (默认1): ").strip()
    
    if choice == "2":
        # 测试搜索几个汉字
        test_chars = ["一", "人", "大", "小", "山"]
        for char in test_chars:
            print(f"\n=== 搜索字符: {char} ===")
            search_by_character(char, top_k=3)
    else:
        interactive_search()
