from astrbot.api.star import Star, Context
from astrbot.api.event import filter, AstrMessageEvent
import aiohttp
from urllib.parse import quote


class SeerPetQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.name = "赛尔号精灵查询"
        self.description = "调用 SeerAPI 查询赛尔号精灵详细属性与信息"
        self.version = "2.0.0"
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

        # 从外层ID字典中取出内层精灵详情对象
        if not raw_data:
            yield event.plain_result(f"未查询到精灵「{pet_name}」的相关数据")
            return
        pet_detail = next(iter(raw_data.values()), {})
        
        formatted_msg = self._format_output(pet_detail, pet_name)
        yield event.plain_result(formatted_msg)

    def _format_output(self, pet: dict, input_name: str) -> str:
        """格式化精灵详情数据，适配QQ纯文本展示"""
        # ========== 1. 基础信息 ==========
        base_stats = pet.get("base_stats", {})
        total_stats = base_stats.get("total", "未知")
        
        # 属性组合ID
        elem_type = pet.get("type", {})
        elem_id = elem_type.get("id", "未知")
        
        # 性别ID转中文
        gender_info = pet.get("gender", {})
        gender_id = gender_info.get("id", "未知")
        gender_map = {0: "无性别", 1: "雄性", 2: "雌性"}
        gender_text = gender_map.get(gender_id, f"ID:{gender_id}")
        
        # 击败获得学习力格式化
        yield_ev = pet.get("yielding_ev", {})
        ev_list = []
        ev_name_map = {
            "atk": "攻击", "def": "防御",
            "sp_atk": "特攻", "sp_def": "特防",
            "spd": "速度", "hp": "体力"
        }
        for k, v in yield_ev.items():
            if k in ("percent", "total") or v == 0:
                continue
            ev_list.append(f"{ev_name_map.get(k, k)}+{v}")
        ev_text = "、".join(ev_list) if ev_list else "无"

        base_part = [
            f"【精灵信息】{pet.get('name', input_name)}",
            "─────────────────────",
            "【基础信息】",
            f"精灵序号：{pet.get('resource_id', '未知')}",
            f"属性组合ID：{elem_id}",
            f"性别：{gender_text}",
            f"种族值总和：{total_stats}",
            f"可捕捉：{'是' if pet.get('catch_rate', 0) > 0 else '否'}",
            f"可放生：{'是' if pet.get('releaseable') else '否'}",
            f"融合素材：主{'可' if pet.get('fusion_master') else '不可'}/副{'可' if pet.get('fusion_sub') else '不可'}",
            f"抗性系统：{'是' if pet.get('has_resistance') else '否'}",
            f"击败获得学习力：{ev_text}",
            "─────────────────────",
        ]

        # ========== 2. 种族值明细 ==========
        stats_part = [
            "【种族值明细】",
            f"体力：{base_stats.get('hp', '未知')}",
            f"攻击：{base_stats.get('atk', '未知')}",
            f"防御：{base_stats.get('def', '未知')}",
            f"特攻：{base_stats.get('sp_atk', '未知')}",
            f"特防：{base_stats.get('sp_def', '未知')}",
            f"速度：{base_stats.get('spd', '未知')}",
            "─────────────────────",
        ]

        # ========== 3. 技能体系 ==========
        skills = pet.get("skill", [])
        skill_count = len(skills)
        fifth_skill = None
        for sk in skills:
            if sk.get("is_fifth"):
                fifth_skill = sk
                break

        skill_part = [
            "【技能体系】",
            f"共包含 {skill_count} 个等级解锁技能",
        ]
        if fifth_skill:
            sk_info = fifth_skill.get("skill", {})
            skill_part.append(
                f"第五技能ID：{sk_info.get('id', '未知')}（{fifth_skill.get('learning_level', '未知')}级解锁）"
            )
        skill_part.append("─────────────────────")

        # ========== 4. 关联资源 ==========
        soulmarks = pet.get("soulmark", [])
        soulmark_ids = [str(s.get("id", "")) for s in soulmarks if s.get("id")]
        soulmark_text = "、".join(soulmark_ids) if soulmark_ids else "无"
        
        encyclopedia = pet.get("encyclopedia_entry", {})
        archive = pet.get("archive_story_entry", {})
        peak_pool = pet.get("peak_pool", {})

        related_part = [
            "【关联资源】",
            f"魂印ID：{soulmark_text}",
            f"图鉴条目ID：{encyclopedia.get('id', '未知')}",
            f"档案故事ID：{archive.get('id', '未知')}",
            f"巅峰归属：{'普通池' if peak_pool.get('id') == 2 else '未知'}",
        ]

        return "\n".join(base_part + stats_part + skill_part + related_part)