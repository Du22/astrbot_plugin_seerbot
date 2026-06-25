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

    @filter.command("精灵")
    async def query_sprite(self, event: AstrMessageEvent, sprite_name: str = ""):
        '''赛尔号精灵图鉴查询，示例：精灵 雷伊'''
        if not sprite_name:
            yield event.plain_result("格式错误！正确示例：精灵 雷伊")
            return

        try:
            def _search():
                # 第一步：MediaWiki 搜索匹配词条
                search_resp = requests.get(
                    self.wiki_base,
                    params={
                        "action": "opensearch",
                        "search": sprite_name,
                        "format": "json",
                        "limit": 1
                    },
                    timeout=10
                )
                search_resp.raise_for_status()
                result = search_resp.json()
                if not result[1]:
                    return None
                
                # 第二步：获取页面摘要
                page_title = result[1][0]
                detail_resp = requests.get(
                    self.wiki_base,
                    params={
                        "action": "query",
                        "prop": "extracts",
                        "exintro": "true",
                        "titles": page_title,
                        "format": "json",
                        "explaintext": "true"
                    },
                    timeout=10
                )
                detail_resp.raise_for_status()
                pages = detail_resp.json()["query"]["pages"]
                page_id = next(iter(pages))
                return {
                    "title": page_title,
                    "intro": pages[page_id].get("extract", "暂无简介")
                }
            
            data = await asyncio.to_thread(_search)
        except Exception as e:
            yield event.plain_result(f"查询失败，网络/接口异常：{str(e)}")
            return

        if not data:
            yield event.plain_result(f"未找到精灵「{sprite_name}」，请检查名称是否完整")
            return

        info_text = "===== 赛尔号精灵图鉴 =====\n"
        info_text += f"名称：{data['title']}\n"
        info_text += f"\n【简介】\n{data['intro'][:300]}..."
        
        yield event.plain_result(info_text)