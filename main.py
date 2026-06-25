import requests
from astrbot.api import AstrBotApi, event, register
from astrbot.api.message_components import Image, Plain

# 注册插件
@register("seer_sprite_query", "赛尔号图鉴查询", "发送「精灵 名称」查询赛尔号精灵信息", "1.0")
class SeerSpriteQuery:
    def __init__(self, api: AstrBotApi):
        self.api = api
        self.api_url = "https://api.seer2.cn/sprite/search"

    @event("message")
    async def on_message(self, message):
        # 获取纯文本消息
        text = message.get_plain_text().strip()
        if not text.startswith("精灵 "):
            return
        
        # 截取精灵名称
        sprite_name = text.replace("精灵 ", "", 1).strip()
        if not sprite_name:
            await message.reply([Plain("格式错误！正确示例：精灵 雷伊")])
            return

        try:
            # 请求图鉴接口
            resp = requests.get(
                self.api_url,
                params={"name": sprite_name},
                timeout=12
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            await message.reply([Plain(f"查询失败，网络/接口异常：{str(e)}")])
            return
        
        # 判断是否查到精灵
        if data.get("code") != 200 or len(data.get("data", [])) == 0:
            await message.reply([Plain(f"未找到精灵「{sprite_name}」，检查名称是否完整")])
            return
        
        sprite = data["data"][0]
        msg_list = []

        # 精灵图片优先发送
        img_url = sprite.get("img")
        if img_url:
            msg_list.append(Image(url=img_url))

        # 基础信息文本拼接
        info_text = "===== 赛尔号精灵图鉴 =====\n"
        info_text += f"名称：{sprite.get('name')}\n"
        info_text += f"精灵ID：{sprite.get('id')}\n"
        info_text += f"属性：{sprite.get('attr')}\n"
        info_text += f"性别：{sprite.get('gender', '无')}\n"
        info_text += f"进化链：{sprite.get('evolve', '无进化')}\n"
        info_text += f"获取途径：{sprite.get('getway', '暂无记录')}\n\n"

        # 种族值
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
        info_text += f"特攻{spatk:3d}特防{spdf:3d} | 速度{speed:3d}\n"
        info_text += f"种族总和：{total}\n\n"

        # 前5个代表技能
        skills = sprite.get("skill", [])[:5]
        info_text += "【代表技能】\n"
        for sk in skills:
            sk_name = sk.get("name", "未知")
            sk_attr = sk.get("attr", "无属性")
            sk_pow = sk.get("power", "--")
            info_text += f"{sk_name} | 属性{sk_attr} | 威力{sk_pow}\n"

        msg_list.append(Plain(info_text))
        # 回复消息
        await message.reply(msg_list)