from astrbot.api.star import Star, Context
from astrbot.api.event import filter, AstrMessageEvent
import aiohttp
from urllib.parse import quote


class SeerPetQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.name = "赛尔号精灵查询"
        self.description = "调用 SeerAPI 查询赛尔号精灵详细属性与信息"
        self.version = "1.1.0"
        self.author = "自定义插件"

    @filter.command("精灵")
    async def query_pet_info(self, event: AstrMessageEvent):
        '''查询赛尔号精灵信息，用法：精灵 精灵名称/精灵ID'''
        message_text = event.message_str.strip()
        parts = message_text.split(maxsplit=1)
        
        if len(parts) < 2:
            yield event.plain_result("请输入要查询的精灵名称，示例：\n/精灵 圣灵谱尼")
            return
        
        pet_name = parts[1].strip()
        encoded_pet = quote(pet_name)
         # 精灵基础信息接口
        api_url = f"https://api.seerapi.com/v1/pet/{encoded_pet}"
        

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(api_url) as resp:
                    if resp.status != 200:
                        yield event.plain_result(f"查询失败：未找到精灵「{pet_name}」，请检查名称/ID是否正确")
                        return
                    raw_data = await resp.json()
        except aiohttp.ClientError:
            yield event.plain_result("网络请求失败，请检查网络连接后重试")
            return
        except Exception as e:
            yield event.plain_result(f"查询异常：{str(e)}")
            return

        formatted_msg = self._format_output(raw_data, pet_name)
        yield event.plain_result(formatted_msg)

    def _format_output(self, raw_data, input_name):
        # 兼容有无外层 data 包裹
        pet = next(iter(raw_data.values()), {})

        # ========== 1. 🗡️基础信息🗡️ ==========
        # 兼容多种种族值字段命名
        stats = pet.get("base_stats", {})
        try:
            total_stats = stats.get("total", {})
        except (TypeError, ValueError):
            total_stats = "未知"

        base_part = [
            f"【精灵信息】{pet.get('name', pet.get('pet_name', input_name))}",
            "─────────────────────",
            "【基础信息】",
            f"精灵序号：{pet.get('resource_id', pet.get('pet_id', '未知'))}",
            f"种族值总和：{total_stats}",
            "─────────────────────",
        ]

        # ========== 2. ⚔️种族值明细⚔️ ==========
        stats_part = [
            "【种族值明细】",
            f"🩸体力：{stats.get('hp', stats.get('vitality', '未知'))}",
            f"🔪攻击：{stats.get('atk', stats.get('attack', '未知'))}",
            f"🛡️防御：{stats.get('def', stats.get('defense', '未知'))}",
            f"🔮特攻：{stats.get('sp_atk', stats.get('satk', stats.get('spatk', '未知')))}",
            f"🔰特防：{stats.get('sp_def', stats.get('sdef', stats.get('spdef', '未知')))}",
            f"🏃速度：{stats.get('spd', stats.get('speed', '未知'))}",
            "─────────────────────",
        ]

        return "\n".join(base_part + stats_part)
    @filter.command("刻印")
    async def query_mintmark_info(self, event: AstrMessageEvent):
        '''查询赛尔号刻印信息，用法：刻印 刻印名称/刻印ID'''
        message_text = event.message_str.strip()
        parts = message_text.split(maxsplit=1)

        if len(parts) < 2:
            yield event.plain_result("请输入要查询的刻印名称，示例：\n/刻印 衡·巨刃")
            return
        
        mintmark_name = parts[1].strip()
        encoded_name = quote(mintmark_name)
        mintmark_url = f"https://api.seerapi.com/v1/mintmark/{encoded_name}"
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(mintmark_url) as resp:
                    if resp.status != 200:
                        yield event.plain_result(f"查询失败：未找到刻印「{mintmark_name}」，请检查名称/ID是否正确")
                        return
                    mintmark_data = await resp.json()
        except aiohttp.ClientError:
            yield event.plain_result("网络请求失败，请检查网络连接后重试")
            return
        except Exception as e:
            yield event.plain_result(f"查询异常：{str(e)}")
            return
        
        formatted_msg = self._format_mintmark_output(mintmark_data, mintmark_name)
        yield event.plain_result(formatted_msg)
    def _format_mintmark_output(self, mintmark_data, input_name):
        # 兼容ID为键的字典结构，遍历所有匹配结果
        mintmark = next(iter(mintmark_data.values()), {})

       # ========== 1. 🗡️基础信息🗡️ ==========
        # 兼容多种种族值字段命名
        mintstats = mintmark.get("base_attr_value", {}) or {}
        mintstats1 = mintmark.get("max_attr_value", {}) or {}
        mintstats2 = mintmark.get("extra_attr_value", {}) or {}
        mint_part = [
            f"【刻印信息】{mintmark.get('name', '未知刻印')}",
            "─────────────────────",
            "【基础信息】",
            f"刻印ID：{mintmark.get('id', '未知')}",
            "【基本数值/满级数值+额外数值】",
            f"🩸体力：{mintstats.get('hp', mintstats.get('vitality', '0'))} / {mintstats1.get('hp', mintstats1.get('vitality', '0'))} + {mintstats2.get('hp', mintstats2.get('vitality', '0'))}",
            f"🔪攻击：{mintstats.get('atk', mintstats.get('attack', '0'))} / {mintstats1.get('atk', mintstats1.get('attack', '0'))} +{mintstats2.get('atk', mintstats2.get('attack', '0'))}",
            f"🛡️防御：{mintstats.get('def', mintstats.get('defense', '0'))} / {mintstats1.get('def', mintstats1.get('defense', '0'))} + {mintstats2.get('def', mintstats2.get('defense', '0'))}",
            f"🔮特攻：{mintstats.get('sp_atk', mintstats.get('satk', mintstats.get('spatk', '0')))} / {mintstats1.get('sp_atk', mintstats1.get('satk', mintstats1.get('spatk', '0')))} + {mintstats2.get('sp_atk', mintstats2.get('satk', mintstats2.get('spatk', '0')))}",
            f"🔰特防：{mintstats.get('sp_def', mintstats.get('sdef', mintstats.get('spdef', '0')))} / {mintstats1.get('sp_def', mintstats1.get('sdef', mintstats1.get('spdef', '0')))} + {mintstats2.get('sp_def', mintstats2.get('sdef', mintstats2.get('spdef', '0')))}",
            f"🏃速度：{mintstats.get('spd', mintstats.get('speed', '0'))} / {mintstats1.get('spd', mintstats1.get('speed', '0'))} + {mintstats2.get('spd', mintstats2.get('speed', '0'))}",
            f"🐉总和：{mintstats.get('total', mintstats.get('total_value', '0'))} / {mintstats1.get('total', mintstats1.get('total_value', '0'))} + {mintstats2.get('total', mintstats2.get('total_value', '0'))}",


            "─────────────────────",
        ]

        return "\n".join(mint_part)