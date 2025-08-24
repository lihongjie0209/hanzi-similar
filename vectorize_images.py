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

def extract_features_from_images(images_dir):
    """从所有图片中提取特征向量"""
    image_paths = glob.glob(os.path.join(images_dir, "*.png"))
    features = []
    filenames = []
    
    print(f"正在处理 {len(image_paths)} 张图片...")
    
    for i, image_path in enumerate(image_paths):
        if i % 1000 == 0:
            print(f"已处理 {i}/{len(image_paths)} 张图片")
        
        try:
            feature = load_and_preprocess_image(image_path)
            features.append(feature)
            filenames.append(os.path.basename(image_path))
        except Exception as e:
            print(f"处理图片 {image_path} 时出错: {e}")
    
    return np.array(features), filenames

def build_vector_database(features, filenames, n_components=100):
    """构建向量数据库"""
    print("正在使用PCA降维...")
    # 使用PCA降维
    pca = PCA(n_components=n_components)
    features_reduced = pca.fit_transform(features)
    
    print("正在构建最近邻索引...")
    # 构建最近邻索引
    nbrs = NearestNeighbors(n_neighbors=10, algorithm='ball_tree').fit(features_reduced)
    
    return pca, nbrs, features_reduced, filenames

def save_vector_database(pca, nbrs, features, filenames, save_path="vector_db.pkl"):
    """保存向量数据库"""
    data = {
        'pca': pca,
        'nbrs': nbrs,
        'features': features,
        'filenames': filenames
    }
    with open(save_path, 'wb') as f:
        pickle.dump(data, f)
    print(f"向量数据库已保存到 {save_path}")

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

if __name__ == "__main__":
    images_dir = "images"
    
    # 提取特征
    features, filenames = extract_features_from_images(images_dir)
    
    # 构建向量数据库
    pca, nbrs, features_reduced, filenames = build_vector_database(features, filenames)
    
    # 保存向量数据库
    save_vector_database(pca, nbrs, features_reduced, filenames)
    
    print("向量数据库构建完成！")
    print(f"共处理了 {len(filenames)} 张图片")
    print(f"特征维度: {features.shape[1]} -> {features_reduced.shape[1]}")
