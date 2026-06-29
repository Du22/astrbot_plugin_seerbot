# 你给出的示例数据结构
data = {
    "soulmark": [
        {
            "id": 753,
            "url": "https://api.seerapi.com/v1/soulmark/753"
        }
    ]
}

# 提取 soulmark 列表第一个元素的 url 字段
soulmark_url = data["soulmark"][0]["url"]
print("提取到的url:", soulmark_url)