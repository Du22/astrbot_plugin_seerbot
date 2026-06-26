from seerapi import SeerAPI
from astrbot.api.star import Context, Star
from astrbot.api.event import filter, AstrMessageEvent

# ========== 配置项 ==========
# 种族值字段中文映射
STAT_TRANSLATION = {
    "hp": "生命",
    "atk": "攻击",
    "def": "防御",
    "sp_atk": "特攻",
    "sp_def": "特防",
    "spd": "速度",
    "total": "总和"
}
# 种族值固定输出顺序
STAT_ORDER = ["hp", "atk", "def", "sp_atk", "sp_def", "spd"]
# 指令列表（用于截取参数）
COMMAND_LIST = ["查精灵", "精灵查询", "seer"]
# ============================

class SeerPetPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("查精灵", aliases=["精灵查询", "seer"])
    async def query_pet(self, event: AstrMessageEvent):
        """赛尔号精灵查询，指令：查精灵 精灵名称"""
        full_text = event.message_str.strip()
        pet_name = ""

        # 遍历所有指令前缀，截取命令后的纯精灵名称
        for cmd in COMMAND_LIST:
            if full_text.lower().startswith(cmd.lower()):
                pet_name = full_text[len(cmd):].strip()
                break

        if not pet_name:
            yield event.plain_result(
                "请输入精灵名称，示例：\n查精灵 谱尼\n查精灵 圣灵谱尼"
            )
            return

        try:
            # 调用 SeerAPI，仅传入纯精灵名称，不带命令
            async with SeerAPI() as client:
                result = await client.get_by_name("pet", pet_name)

            # 未找到结果
            if not result:
                yield event.plain_result(
                    f"未找到名为「{pet_name}」的精灵，请检查名称是否正确。"
                )
                return
            
            # 兼容返回列表/单个对象
            pet = result[0] if isinstance(result, list) else result

            # 兼容属性对象与字典两种结构
            base_stats = pet.base_stats
            if hasattr(base_stats, "__dict__"):
                stats_dict = {
                    k: v for k, v in base_stats.__dict__.items()
                    if not k.startswith("_") and isinstance(v, (int, float))
                }
            else:
                stats_dict = dict(base_stats)

            # 格式化种族值
            stats_lines = []
            calc_total = 0
            for key in STAT_ORDER:
                if key in stats_dict:
                    value = stats_dict[key]
                    cn_name = STAT_TRANSLATION[key]
                    stats_lines.append(f"{cn_name}：{value}")
                    calc_total += value

            # 优先使用接口返回的总和，无则自动计算
            total = stats_dict.get("total", calc_total)

            # 排版输出
            reply = (
                "===== 精灵查询结果 =====\n"
                f"精灵名称：{pet.name}\n"
                f"精灵ID：{pet.id}\n"
                "------------------------\n"
                "          种族值\n"
                "------------------------\n"
                + "\n".join(stats_lines) +
                "\n------------------------\n"
                f"种族值总和：{total}"
            )

            yield event.plain_result(reply)

        except Exception as e:
            yield event.plain_result(
                f"查询失败：{str(e)}\n请稍后重试，或确认精灵名称、API 服务是否正常。"
            )