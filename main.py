import requests
from urllib.parse import quote

def get_seer_pet_id(pet_name: str):
    """
    调用SeerAPI精灵接口，提取resource_id（精灵ID）
    :param pet_name: 赛尔号精灵中文名称
    :return: 精灵ID；请求/解析失败时返回None
    """
    url = f"https://api.seerapi.com/v1/pet/{quote(pet_name)}"
    
    # 兼容部分接口要求的请求头，避免返回非JSON格式
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        # 发送请求并校验状态
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        # 解析JSON响应
        json_data = resp.json()

        # 兼容两种常见返回结构：
        # 1. 顶层直接有 resource_id
        # 2. 嵌套在 data 字段中（标准REST风格）
        resource_id = json_data.get("resource_id")
        if resource_id is None and "data" in json_data:
            resource_id = json_data["data"].get("resource_id")

        return resource_id

    except requests.exceptions.RequestException as e:
        print(f"接口请求失败: {e}")
        return None
    except ValueError as e:
        print(f"返回内容不是合法JSON: {e}")
        return None

# 调用示例
if __name__ == "__main__":
    pet_name = "谱尼"  # 替换为目标精灵名称
    pet_id = get_seer_pet_id(pet_name)
    if pet_id is not None:
        print(f"精灵「{pet_name}」的resource_id = {pet_id}")
    else:
        print("未能获取到精灵ID")