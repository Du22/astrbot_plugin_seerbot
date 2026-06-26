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
# 指令前缀列表（用于精准截取纯精灵名称）
COMMAND_PREFIXES = ["查精灵", "精灵查询", "seer"]
# ============================

class SeerPetPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("查精灵", aliases=["精灵查询", "seer"])
    async def query_pet(self, event: AstrMessageEvent):
        """赛尔号精灵查询，指令：查精灵 精灵名称"""
        full_text = event.message_str.strip()
        pet_name = ""

        # 精准移除命令前缀，仅保留纯精灵名称传给 API
        for cmd in COMMAND_PREFIXES:
            if full_text.lower().startswith(cmd.lower()):
                pet_name = full_text[len(cmd):].strip()
                break

        if not pet_name:
            yield event.plain_result(
                "请输入精灵名称，示例：\n查精灵 谱尼\n查精灵 圣灵谱尼"
            )
            return

        try:
            # 调用 SeerAPI，第二个参数仅为纯精灵名称，不含任何命令，返回值直接赋值为 pet
            async with SeerAPI() as client:
                pet = await client.get_by_name('pet', pet_name)
               

            # 兼容 API 嵌套 data 结构，解决 'data' 键报错
            if isinstance(pet, dict) and "data" in pet:
                pet = pet["data"]

            # 未找到结果兜底
            if not pet:
                yield event.plain_result(
                    f"未找到名为「{pet_name}」的精灵，请检查名称是否正确。"
                )
                return
            
            # 兼容返回列表/单个对象两种格式，列表取第一条结果
            if isinstance(pet, list):
                pet = pet[0]

            # 兼容 base_stats 的对象属性/字典两种结构
            if hasattr(pet, "base_stats"):
                base_stats = pet.base_stats
            else:
                base_stats = pet.get("base_stats", {})

            if hasattr(base_stats, "__dict__"):
                stats_dict = {
                    k: v for k, v in base_stats.__dict__.items()
                    if not k.startswith("_") and isinstance(v, (int, float))
                }
            elif isinstance(base_stats, dict):
                stats_dict = base_stats
            else:
                stats_dict = {}

            # 按固定顺序格式化种族值
            stats_lines = []
            calc_total = 0
            for key in STAT_ORDER:
                if key in stats_dict:
                    value = stats_dict[key]
                    cn_name = STAT_TRANSLATION[key]
                    stats_lines.append(f"{cn_name}：{value}")
                    calc_total += value

            # 优先用接口返回的总和，无则自动计算
            total = stats_dict.get("total", calc_total)

            # 统一排版输出
            reply = (
                "===== 精灵查询结果 =====\n"
                f"精灵名称：{pet.name if hasattr(pet, 'name') else pet.get('name', '未知')}\n"
                f"精灵ID：{pet.id if hasattr(pet, 'id') else pet.get('id', '未知')}\n"
                "------------------------\n"
                "          种族值\n"
                "------------------------\n"
                + "\n".join(stats_lines) +
                "\n------------------------\n"
                f"种族值总和：{total}"
            )

            yield event.plain_result(reply)

        except KeyError as e:
            yield event.plain_result(
                f"API 返回结构异常：缺少字段 {str(e)}\n请确认 SeerAPI 版本或稍后重试。"
            )
        except Exception as e:
            yield event.plain_result(
                f"查询失败：{str(e)}\n请稍后重试，或确认精灵名称、API 服务是否正常。"
            )