import os
import numpy as np
from PIL import Image
import pickle

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

def find_character_similarity(char1, char2):
    """查找两个字符的相似度"""
    # 获取Unicode码
    code1 = f"{ord(char1):04X}"
    code2 = f"{ord(char2):04X}"
    
    print(f"字符1: {char1} (U+{code1})")
    print(f"字符2: {char2} (U+{code2})")
    
    # 检查图片是否存在
    img1_path = f"images/{code1}.png"
    img2_path = f"images/{code2}.png"
    
    if not os.path.exists(img1_path):
        print(f"图片 {img1_path} 不存在")
        return
    
    if not os.path.exists(img2_path):
        print(f"图片 {img2_path} 不存在")
        return
    
    # 加载向量数据库
    pca, nbrs, features, filenames = load_vector_database()
    
    # 找到两个字符在数据库中的索引
    try:
        idx1 = filenames.index(f"{code1}.png")
        idx2 = filenames.index(f"{code2}.png")
    except ValueError as e:
        print(f"在向量数据库中找不到字符: {e}")
        return
    
    # 计算降维后特征的欧几里得距离
    feature1 = features[idx1]
    feature2 = features[idx2]
    distance = np.linalg.norm(feature1 - feature2)
    
    print(f"在向量数据库中的距离: {distance:.4f}")
    
    # 查找 char1 的相似字符，看 char2 是否在其中
    distances, indices = nbrs.kneighbors(feature1.reshape(1, -1), n_neighbors=20)
    
    print(f"\n查找 {char1} 的前20个相似字符:")
    found_char2 = False
    for i, idx in enumerate(indices[0]):
        unicode_code = filenames[idx].replace('.png', '')
        char = chr(int(unicode_code, 16))
        dist = distances[0][i]
        marker = " ★" if char == char2 else ""
        print(f"{i+1:2d}. {unicode_code} (字符: {char}) - 距离: {dist:.4f}{marker}")
        if char == char2:
            found_char2 = True
    
    if not found_char2:
        print(f"\n{char2} 不在 {char1} 的前20个相似字符中")

if __name__ == "__main__":
    # 检查 '行' 和 '⾏' 的相似度
    char1 = '行'  # U+884C
    char2 = '⾏'  # U+2F8F
    
    find_character_similarity(char1, char2)
