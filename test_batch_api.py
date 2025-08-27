#!/usr/bin/env python3
"""测试批量查询API接口"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_batch_char_search():
    """测试批量字符查询"""
    print("=== 测试批量字符查询 ===")
    
    payload = {
        "chars": ["人", "工", "智", "能"],
        "top_k": 3
    }
    
    response = requests.post(f"{BASE_URL}/search/batch/char", json=payload)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"查询字符: {result['queries']}")
        print(f"结果数量: {len(result['results'])}")
        
        for i, (query, results) in enumerate(zip(result['queries'], result['results'])):
            print(f"\n字符 '{query}' 的相似字符:")
            for j, item in enumerate(results[:3], 1):
                print(f"  {j}. {item['char']} ({item['unicode']}) - 距离: {item['distance']:.4f}")
    else:
        print(f"错误: {response.text}")

def test_batch_unicode_search():
    """测试批量Unicode查询"""
    print("\n=== 测试批量Unicode查询 ===")
    
    payload = {
        "unicodes": ["U+4E00", "U+4E01", "U+4E02", "U+4E03"],
        "top_k": 2
    }
    
    response = requests.post(f"{BASE_URL}/search/batch/unicode", json=payload)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"查询字符: {result['queries']}")
        print(f"结果数量: {len(result['results'])}")
        
        for i, (query, results) in enumerate(zip(result['queries'], result['results'])):
            print(f"\n字符 '{query}' 的相似字符:")
            for j, item in enumerate(results, 1):
                print(f"  {j}. {item['char']} ({item['unicode']}) - 距离: {item['distance']:.4f}")
    else:
        print(f"错误: {response.text}")

def test_healthz():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    
    response = requests.get(f"{BASE_URL}/healthz")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"服务状态: {'正常' if result['ok'] else '异常'}")
        print(f"向量数据库: {'已初始化' if result.get('vector_db_initialized') else '未初始化'}")
        print(f"SVG渲染器: {'已初始化' if result.get('svg_renderer_initialized') else '未初始化'}")
        if 'total_images' in result:
            print(f"向量数据总数: {result['total_images']}")
    else:
        print(f"错误: {response.text}")

if __name__ == "__main__":
    try:
        test_healthz()
        test_batch_char_search()
        test_batch_unicode_search()
        print("\n✅ 所有测试完成")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 请确保API服务器在 http://127.0.0.1:8000 上运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
