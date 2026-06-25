import asyncio
import requests
import re
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain


class SeerSpriteQuery(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.wiki_api = "https://wiki.biligame.com/seer/api.php"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }

    @filter.command("精灵")
    async def query_sprite(self, event: AstrMessageEvent, sprite_name: str = ""):
        '''赛尔号精灵图鉴查询，示例：精灵 雷伊'''
        if not sprite_name:
            yield event.plain_result("格式错误！正确示例：精灵 雷伊")
            return

        try:
            def _fetch_data():
                # 1. 搜索匹配词条，自动处理重定向
                search_resp = requests.get(
                    self.wiki_api,
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": sprite_name,
                        "srwhat": "title",
                        "srlimit": 1,
                        "format": "json"
                    },
                    headers=self.headers,
                    timeout=10
                )
                search_resp.raise_for_status()
                search_data = search_resp.json()
                if not search_data["query"]["search"]:
                    return None

                page_title = search_data["query"]["search"][0]["title"]

                # 2. 获取页面解析内容
                parse_resp = requests.get(
                    self.wiki_api,
                    params={
                        "action": "parse",
                        "page": page_title,
                        "format": "json",
                        "prop": "text",
                        "disableeditsection": 1,
                        "redirects": 1
                    },
                    headers=self.headers,
                    timeout=12
                )
                parse_resp.raise_for_status()
                html = parse_resp.json()["parse"]["text"]["*"]

                # 3. 清理HTML工具函数
                def clean_text(raw: str) -> str:
                    raw = re.sub(r"<[^>]+>", "", raw)
                    raw = raw.replace("&nbsp;", " ").replace("&amp;", "&")
                    return raw.strip()

                # 4. 提取infobox基础信息
                info = {"name": page_title}

                # 匹配所有infobox行
                info_rows = re.findall(
                    r"<tr[^>]*>\s*<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>\s*</tr>",
                    html, re.S
                )
                for label, value in info_rows:
                    label = clean_text(label)
                    value = clean_text(value)
                    if "编号" in label or "ID" in label:
                        info["id"] = value
                    elif "属性" in label:
                        info["attr"] = value
                    elif "性别" in label:
                        info["gender"] = value
                    elif "进化" in label:
                        info["evolve"] = value[:60]  # 限制长度
                    elif "获得" in label or "获取" in label:
                        info["getway"] = value[:60]

                # 5. 提取种族值
                race = {"hp": 0, "atk": 0, "def": 0, "spatk": 0, "spdef": 0, "speed": 0}
                race_patterns = [
                    ("hp", r"体力[^0-9]*(\d+)"),
                    ("atk", r"攻击[^0-9]*(\d+)"),
                    ("def", r"防御[^0-9]*(\d+)"),
                    ("spatk", r"特攻[^0-9]*(\d+)"),
                    ("spdef", r"特防[^0-9]*(\d+)"),
                    ("speed", r"速度[^0-9]*(\d+)"),
                ]
                for key, pattern in race_patterns:
                    match = re.search(pattern, html, re.S)
                    if match:
                        race[key] = int(match.group(1))

                # 6. 提取前5个技能（匹配技能表格）
                skills = []
                # 匹配技能表行：技能名 | 属性 | 威力 | PP | 效果
                skill_rows = re.findall(
                    r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>",
                    html, re.S
                )
                for row in skill_rows:
                    name = clean_text(row[0])
                    attr = clean_text(row[1])
                    power = clean_text(row[2])
                    # 过滤表头和非技能行
                    if not name or "技能" in name or "名称" in name or len(name) > 15:
                        continue
                    skills.append({"name": name, "attr": attr, "power": power})
                    if len(skills) >= 5:
                        break

                return {
                    "info": info,
                    "race": race,
                    "skills": skills
                }

            data = await asyncio.to_thread(_fetch_data)
        except Exception as e:
            yield event.plain_result(f"查询失败，接口异常：{str(e)}")
            return

        if not data:
            yield event.plain_result(f"未找到精灵「{sprite_name}」，请检查名称是否完整")
            return

        # 拼接输出文本
        info = data["info"]
        race = data["race"]
        skills = data["skills"]

        info_text = "===== 赛尔号精灵图鉴 =====\n"
        info_text += f"名称：{info.get('name')}\n"
        info_text += f"精灵ID：{info.get('id', '暂无')}\n"
        info_text += f"属性：{info.get('attr', '未知')}\n"
        info_text += f"性别：{info.get('gender', '无')}\n"
        info_text += f"进化链：{info.get('evolve', '无进化')}\n"
        info_text += f"获取途径：{info.get('getway', '暂无记录')}\n\n"

        # 种族值计算
        hp = race["hp"]
        atk = race["atk"]
        df = race["def"]
        spatk = race["spatk"]
        spdf = race["spdef"]
        speed = race["speed"]
        total = hp + atk + df + spatk + spdf + speed

        info_text += "【种族值】\n"
        info_text += f"体力{hp:3d} 攻击{atk:3d} | 防御{df:3d}\n"
        info_text += f"特攻{spatk:3d} 特防{spdf:3d} | 速度{speed:3d}\n"
        info_text += f"种族总和：{total}\n\n"

        # 代表技能
        info_text += "【代表技能】\n"
        if skills:
            for sk in skills:
                info_text += f"{sk['name']} | 属性{sk['attr']} | 威力{sk['power']}\n"
        else:
            info_text += "暂无技能数据\n"

        yield event.plain_result(info_text)