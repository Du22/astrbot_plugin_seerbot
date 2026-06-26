from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from seerapi import SeerAPI
import asyncio


class SeerPetQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("查精灵")
    async def query_pet(self, event: AstrMessageEvent):
        """
        赛尔号精灵查询指令
        用法：/查精灵 <精灵名称>
        功能：按名称查询精灵ID与基础信息，支持单/多匹配结果
        """
        # 自主解析参数，兼容带空格的精灵名称
        msg_parts = event.message_str.split(maxsplit=1)
        if len(msg_parts) < 2 or not msg_parts[1].strip():
            yield event.plain_result("⚠️ 指令参数缺失\n使用示例：/查精灵 谱尼")
            return

        pet_name = msg_parts[1].strip()

        try:
            # 调用 SeerAPI 异步查询
            async with SeerAPI() as client:
                result = await client.get_by_name('pet', pet_name)

            # 无结果处理
            if not result:
                yield event.plain_result(
                    f"❌ 未找到名为「{pet_name}」的精灵\n请检查名称拼写是否正确"
                )
                return

            # 排版构建：适配单结果/多结果场景
            reply_lines = ["🔍 赛尔号精灵查询结果", "───────────────"]

            if isinstance(result, list):
                # 多匹配结果：自动编号列出
                reply_lines.append(f"共找到 {len(result)} 个匹配结果：\n")
                for index, pet in enumerate(result, start=1):
                    reply_lines.append(f"{index}. 精灵名称：{pet.name}")
                    reply_lines.append(f"   精灵ID：{pet.id}\n")
            else:
                # 单匹配结果：清晰字段展示
                reply_lines.append(f"精灵名称：{result.name}")
                reply_lines.append(f"精灵ID：{result.id}")

            reply_lines.append("───────────────")
            yield event.plain_result("\n".join(reply_lines))

        except Exception as e:
            # 全局异常捕获，避免插件崩溃
            yield event.plain_result(f"❌ 查询失败：{str(e)}\n请稍后重试或检查API服务状态")