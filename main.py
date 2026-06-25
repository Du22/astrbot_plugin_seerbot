import asyncio
import requests
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain


class SeerSpriteQuery(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "https://api.seer2.cn/sprite/search"

    @filter.command("精灵")
    async def query_sprite(self, event: AstrMessageEvent, sprite_name: str = ""):
        '''赛尔号精灵图鉴查询，示例：精灵 雷伊'''
        if not sprite_name:
            yield event.plain_result("格式错误！正确示例：精灵 雷伊")
            return

        try:
            # 将同步请求放入线程执行，避免阻塞机器人事件循环
            def _request_api():
                resp = requests.get(
                    self.api_url,
                    params={"name": sprite_name},
                    timeout=12
                )
                resp.raise_for_status()
                return resp.json()
            
            data = await asyncio.to_thread(_request_api)
        except Exception as e:
            yield event.plain_result(f"查询失败，网络/接口异常：{str(e)}")
            return

        # 校验返回结果
        if data.get("code") != 200 or len(data.get("data", [])) == 0:
            yield event.plain_result(f"未找到精灵「{sprite_name}」，请检查名称是否完整")
            return

        sprite = data["data"][0]

        # 拼接基础信息
        info_text = "===== 赛尔号精灵图鉴 =====\n"
        info_text += f"名称：{sprite.get('name')}\n"
        info_text += f"精灵ID：{sprite.get('id')}\n"
        info_text += f"属性：{sprite.get('attr')}\n"
        info_text += f"性别：{sprite.get('gender', '无')}\n"
        info_text += f"进化链：{sprite.get('evolve', '无进化')}\n"
        info_text += f"获取途径：{sprite.get('getway', '暂无记录')}\n\n"

        # 种族值计算与排版
        race = sprite.get("race", {})
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

        # 前5个代表技能
        skills = sprite.get("skill", [])[:5]
        info_text += "【代表技能】\n"
        for sk in skills:
            sk_name = sk.get("name", "未知")
            sk_attr = sk.get("attr", "无属性")
            sk_pow = sk.get("power", "--")
            info_text += f"{sk_name} | 属性{sk_attr} | 威力{sk_pow}\n"

        yield event.plain_result(info_text)