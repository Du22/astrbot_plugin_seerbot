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
                # 1. 主搜索路径
                search_resp = requests.get(
                    self.wiki_api,
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": sprite_name,
                        "srnamespace": "0",
                        "srlimit": "3",
                        "format": "json"
                    },
                    headers=self.headers,
                    timeout=10
                )
                search_resp.raise_for_status()
                search_data = search_resp.json()

                if "error" in search_data:
                    raise RuntimeError(f"搜索接口错误：{search_data['error'].get('info', '未知错误')}")
                if "query" not in search_data or not search_data["query"]["search"]:
                    # 降级到 opensearch
                    return self._fallback_search(sprite_name)

                page_title = search_data["query"]["search"][0]["title"]

                # 2. 获取页面HTML
                parse_resp = requests.get(
                    self.wiki_api,
                    params={
                        "action": "parse",
                        "page": page_title,
                        "format": "json",
                        "prop": "text",
                        "disableeditsection": "1",
                        "redirects": "1"
                    },
                    headers=self.headers,
                    timeout=12
                )
                parse_resp.raise_for_status()
                parse_data = parse_resp.json()

                if "error" in parse_data:
                    raise RuntimeError(f"页面解析错误：{parse_data['error'].get('info', '未知错误')}")

                html = parse_data["parse"]["text"]["*"]
                return self._parse_sprite_html(html, page_title)

            data = await asyncio.to_thread(_fetch_data)
        except Exception as e:
            yield event.plain_result(f"查询失败，接口异常：{str(e)}")
            return

        if not data:
            yield event.plain_result(f"未找到精灵「{sprite_name}」，请检查名称是否完整")
            return

        # 输出拼接
        info = data["info"]
        race = data["race"]
        skills = data["skills"]

        info_text = "===== 赛尔号精灵图鉴 =====\n"
        info_text += f"名称：{info.get('name')}\n"
        info_text += f"精灵序号：{info.get('id', '暂无')}\n"
        info_text += f"属性：{info.get('attr', '未知')}\n"
        info_text += f"性别：{info.get('gender', '无')}\n"
        info_text += f"进化链：{info.get('evolve', '无进化')}\n"
        info_text += f"获取途径：{info.get('getway', '暂无记录')}\n\n"

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

        info_text += "【代表技能】\n"
        if skills:
            for sk in skills:
                info_text += f"{sk['name']} | 属性{sk['attr']} | 威力{sk['power']}\n"
        else:
            info_text += "暂无技能数据\n"

        yield event.plain_result(info_text)

    # ========== 核心：统一的HTML解析逻辑（消除重复代码） ==========
    def _parse_sprite_html(self, html, page_title):
        def clean_text(raw: str) -> str:
            raw = re.sub(r"<[^>]+>", "", raw)
            raw = raw.replace("&nbsp;", " ").replace("&amp;", "&")
            raw = re.sub(r"\s+", " ", raw)
            return raw.strip()

        info = {"name": page_title}

        # 1. 提取infobox基础信息
        info_rows = re.findall(
            r"<tr[^>]*>\s*<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>\s*</tr>",
            html, re.S
        )
        getway_parts = []
        for label, value in info_rows:
            label = clean_text(label)
            value = clean_text(value)
            if not label or not value:
                continue

            # 精灵序号（ID）：优先精确匹配"精灵序号"，兼容其他编号写法
            if label == "精灵序号" or "序号" in label or "编号" in label:
                # 只提取数字部分
                id_match = re.search(r"\d+", value)
                if id_match:
                    info["id"] = id_match.group()

            # 精灵属性
            elif "精灵属性" in label or (label.endswith("属性") and len(label) <= 6):
                info["attr"] = value

            # 性别
            elif "性别" == label or "精灵性别" == label:
                info["gender"] = value

            # 进化链
            elif "进化" in label and "形态" in label:
                info["evolve"] = value[:80]

            # 获取途径：收集所有相关行合并，解决信息不全问题
            elif any(k in label for k in ["获得方式", "获取方式", "入手方式", "获取途径", "获得途径"]):
                getway_parts.append(value)

        if getway_parts:
            info["getway"] = "；".join(getway_parts)[:150]

        # 2. 修复种族值：先定位种族值表格，再提取数值，避免全局误匹配
        race = {"hp": 0, "atk": 0, "def": 0, "spatk": 0, "spdef": 0, "speed": 0}
        # 定位种族值专属表格区域
        race_table_match = re.search(
            r"(种族值|种族数据).*?<table[^>]*>(.*?)</table>",
            html, re.S | re.I
        )
        race_html = race_table_match.group(2) if race_table_match else html

        race_patterns = [
            ("hp", r"体力\D*(\d+)"),
            ("atk", r"攻击\D*(\d+)"),
            ("def", r"防御\D*(\d+)"),
            ("spatk", r"特攻\D*(\d+)"),
            ("spdef", r"特防\D*(\d+)"),
            ("speed", r"速度\D*(\d+)"),
        ]
        for key, pattern in race_patterns:
            match = re.search(pattern, race_html, re.S)
            if match:
                race[key] = int(match.group(1))

        # 3. 修复技能重复：定位技能表 + 名称去重 + 严格过滤
        skills = []
        seen_names = set()
        # 定位技能表区域
        skill_table_match = re.search(
            r"(技能表|技能列表).*?<table[^>]*>(.*?)</table>",
            html, re.S | re.I
        )
        skill_html = skill_table_match.group(2) if skill_table_match else html

        skill_rows = re.findall(
            r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>",
            skill_html, re.S
        )
        for row in skill_rows:
            name = clean_text(row[0])
            attr = clean_text(row[1])
            power = clean_text(row[2])

            # 过滤表头、无效行
            if not name or len(name) > 15:
                continue
            if any(k in name for k in ["技能", "名称", "威力", "属性", "等级", "PP", "效果"]):
                continue
            if re.match(r"^[\d\W]+$", name):
                continue

            # 名称去重，解决重复问题
            if name not in seen_names:
                seen_names.add(name)
                skills.append({"name": name, "attr": attr, "power": power})
                if len(skills) >= 5:
                    break

        return {
            "info": info,
            "race": race,
            "skills": skills
        }

    # 降级搜索方案：opensearch
    def _fallback_search(self, sprite_name):
        try:
            resp = requests.get(
                self.wiki_api,
                params={
                    "action": "opensearch",
                    "search": sprite_name,
                    "namespace": "0",
                    "limit": "1",
                    "format": "json"
                },
                headers=self.headers,
                timeout=10
            )
            resp.raise_for_status()
            result = resp.json()
            if not result[1]:
                return None

            page_title = result[1][0]
            parse_resp = requests.get(
                self.wiki_api,
                params={
                    "action": "parse",
                    "page": page_title,
                    "format": "json",
                    "prop": "text",
                    "disableeditsection": "1",
                    "redirects": "1"
                },
                headers=self.headers,
                timeout=12
            )
            parse_resp.raise_for_status()
            parse_data = parse_resp.json()
            if "error" in parse_data:
                return None

            html = parse_data["parse"]["text"]["*"]
            return self._parse_sprite_html(html, page_title)
        except:
            return None