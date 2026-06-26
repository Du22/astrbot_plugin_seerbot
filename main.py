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

        # ========== 1. 基础信息 ==========
        # 兼容多种种族值字段命名
        stats = pet.get("base_stats", {})
        try:
            total_stats = pet.get("total", sum(stats.values()))
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

        # ========== 2. 种族值明细 ==========
        stats_part = [
            "【种族值明细】",
            f"体力：{stats.get('hp', stats.get('vitality', '未知'))}",
            f"攻击：{stats.get('atk', stats.get('attack', '未知'))}",
            f"防御：{stats.get('def', stats.get('defense', '未知'))}",
            f"特攻：{stats.get('sp_atk', stats.get('satk', stats.get('spatk', '未知')))}",
            f"特防：{stats.get('sp_def', stats.get('sdef', stats.get('spdef', '未知')))}",
            f"速度：{stats.get('spd', stats.get('speed', '未知'))}",
            "─────────────────────",
        ]

        # ========== 3. 技能体系 ==========
        skills = pet.get("skills", pet.get("skill_list", []))
        skill_count = len(skills)
        fifth_skill = None
        for skill in skills:
            if skill.get("level", 0) >= 80:
                fifth_skill = skill
                break

        skill_part = [
            "【技能体系】",
            f"共包含 {skill_count} 个等级解锁技能",
        ]
        if fifth_skill:
            skill_part.append(
                f"第五技能ID：{fifth_skill.get('id', '未知')}（{fifth_skill.get('level', '未知')}级解锁）"
            )
        skill_part.append("─────────────────────")

        # ========== 4. 关联资源 ==========
        related_part = [
            "【关联资源】",
            f"魂印ID：{pet.get('soulmark_id', pet.get('soul_id', '无'))}",
            f"图鉴ID：{pet.get('dex_id', pet.get('book_id', '未知'))}",
            f"巅峰归属：{'普通池' if pet.get('peak_pool_id') == 2 else '未知'}",
        ]

        return "\n".join(base_part + stats_part + skill_part + related_part)