import asyncio
import requests
import re
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain


class SeerSpriteQuery(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.wiki_base = "https://wiki.biligame.com/seer/api.php"
        # 模拟浏览器请求头，避免被WIKI拦截
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @filter.command("精灵")
    async def query_sprite(self, event: AstrMessageEvent, sprite_name: str = ""):
        '''赛尔号精灵图鉴查询，示例：精灵 雷伊'''
        if not sprite_name:
            yield event.plain_result("格式错误！正确示例：精灵 雷伊")
            return

        try:
            def _search():
                # ========== 第一步：搜索匹配词条，自动处理重定向 ==========
                search_resp = requests.get(
                    self.wiki_base,
                    params={
                        "action": "opensearch",
                        "search": sprite_name,
                        "format": "json",
                        "limit": 3
                    },
                    headers=self.headers,
                    timeout=10
                )
                search_resp.raise_for_status()
                result = search_resp.json()
                if not result[1]:
                    return None

                page_title = result[1][0]

                # 解析重定向，获取真实主词条
                redirect_resp = requests.get(
                    self.wiki_base,
                    params={
                        "action": "query",
                        "titles": page_title,
                        "redirects": "1",
                        "format": "json"
                    },
                    headers=self.headers,
                    timeout=10
                )
                redirect_resp.raise_for_status()
                redirect_data = redirect_resp.json()
                pages = redirect_data["query"]["pages"]
                page_id = next(iter(pages))
                if page_id == "-1":
                    return None
                real_title = pages[page_id]["title"]

                # ========== 第二步：获取页面完整HTML，解析结构化数据 ==========
                parse_resp = requests.get(
                    self.wiki_base,
                    params={
                        "action": "parse",
                        "page": real_title,
                        "format": "json",
                        "prop": "text",
                        "disableeditsection": "1"
                    },
                    headers=self.headers,
                    timeout=10
                )
                parse_resp.raise_for_status()
                html = parse_resp.json()["parse"]["text"]["*"]

                # ========== 第三步：正则提取精灵核心数据 ==========
                # 清理HTML标签的辅助函数
                def _clean_html(raw: str) -> str:
                    raw = re.sub(r"<.*?>", "", raw)
                    raw = raw.replace("&nbsp;", " ").strip()
                    return raw

                # 提取infobox基础信息
                info = {"name": real_title}
                
                # 精灵ID
                id_match = re.search(r"精灵编号.*?<td.*?>(.*?)</td>", html, re.S)
                if id_match:
                    info["id"] = _clean_html(id_match.group(1))
                
                # 属性
                attr_match = re.search(r"精灵属性.*?<td.*?>(.*?)</td>", html, re.S)
                if attr_match:
                    info["attr"] = _clean_html(attr_match.group(1))
                
                # 性别
                gender_match = re.search(r"性别.*?<td.*?>(.*?)</td>", html, re.S)
                if gender_match:
                    info["gender"] = _clean_html(gender_match.group(1))
                
                # 进化链
                evolve_match = re.search(r"进化形态.*?<td.*?>(.*?)</td>", html, re.S)
                if evolve_match:
                    info["evolve"] = _clean_html(evolve_match.group(1))
                
                # 获取途径
                getway_match = re.search(r"获得方式.*?<td.*?>(.*?)</td>", html, re.S)
                if getway_match:
                    info["getway"] = _clean_html(getway_match.group(1))[:50]  # 限制长度

                # 提取种族值
                race = {}
                race_patterns = {
                    "hp": r"体力.*?(\d+)",
                    "atk": r"攻击.*?(\d+)",
                    "def": r"防御.*?(\d+)",
                    "spatk": r"特攻.*?(\d+)",
                    "spdef": r"特防.*?(\d+)",
                    "speed": r"速度.*?(\d+)"
                }
                for key, pattern in race_patterns.items():
                    match = re.search(pattern, html, re.S)
                    race[key] = int(match.group(1)) if match else 0

                # 提取前5个技能
                skills = []
                skill_rows = re.findall(
                    r"<tr.*?>.*?<td.*?>(.*?)</td>.*?<td.*?>(.*?)</td>.*?<td.*?>(.*?)</td>",
                    html, re.S
                )
                for row in skill_rows[:8]:
                    name = _clean_html(row[0])
                    attr = _clean_html(row[1])
                    power = _clean_html(row[2])
                    if name and "技能" not in name and len(name) < 20:
                        skills.append({"name": name, "attr": attr, "power": power})
                    if len(skills) >= 5:
                        break

                return {
                    "info": info,
                    "race": race,
                    "skills": skills
                }

            data = await asyncio.to_thread(_search)
        except Exception as e:
            yield event.plain_result(f"查询失败，网络/接口异常：{str(e)}")
            return

        if not data:
            yield event.plain_result(f"未找到精灵「{sprite_name}」，请检查名称是否完整")
            return

        # ========== 第四步：拼接输出文本，对齐原图鉴格式 ==========
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

        # 种族值计算与排版
        hp = race.get("hp", 0)
        atk = race.get("atk", 0)
        df = race.get("def", 0)
        spatk = race.get("spatk", 0)
        spdf = race.get("spdef", 0)
        speed = race.get("speed", 0)
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