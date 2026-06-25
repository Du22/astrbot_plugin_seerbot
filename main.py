from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain
from seerapi import SeerAPI


class SeerSpriteQuery(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_client = SeerAPI()

    @filter.command("精灵")
    async def query_sprite(self, event: AstrMessageEvent, sprite_name: str = ""):
        '''赛尔号精灵图鉴查询，示例：精灵 雷伊'''
        if not sprite_name:
            yield event.plain_result("格式错误！正确示例：精灵 雷伊")
            return

        try:
            async with self.api_client as client:
                # 按名称模糊搜索精灵
                pet_list = await client.list("pet", name=sprite_name)
                if not pet_list:
                    yield event.plain_result(f"未找到精灵「{sprite_name}」，请检查名称是否完整")
                    return

                # 获取首条匹配结果的完整详情
                pet_id = pet_list[0]["id"]
                pet_detail = await client.get("pet", id=pet_id)
        except Exception as e:
            yield event.plain_result(f"查询失败，接口异常：{str(e)}")
            return

        # 基础信息拼接
        info_text = "===== 赛尔号精灵图鉴 =====\n"
        info_text += f"名称：{pet_detail.get('name')}\n"
        info_text += f"精灵ID：{pet_detail.get('id')}\n"
        info_text += f"属性：{pet_detail.get('attr')}\n"
        info_text += f"性别：{pet_detail.get('gender', '无')}\n"
        info_text += f"进化链：{pet_detail.get('evolve', '无进化')}\n"
        info_text += f"获取途径：{pet_detail.get('getway', '暂无记录')}\n\n"

        # 种族值计算
        race = pet_detail.get("race", {})
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
        skills = pet_detail.get("skill", [])[:5]
        info_text += "【代表技能】\n"
        for sk in skills:
            sk_name = sk.get("name", "未知")
            sk_attr = sk.get("attr", "无属性")
            sk_pow = sk.get("power", "--")
            info_text += f"{sk_name} | 属性{sk_attr} | 威力{sk_pow}\n"

        yield event.plain_result(info_text)