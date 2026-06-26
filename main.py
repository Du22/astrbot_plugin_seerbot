from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star
from astrbot.api import logger
from seerapi import SeerAPI
from typing import AsyncGenerator


class SeerPetQueryPlugin(Star):
    """赛尔号精灵查询插件，通过精灵名称查询精灵基础信息"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("赛尔号精灵查询插件已加载")

    @filter.command("查精灵")
    async def query_pet(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
        """查询赛尔号精灵基础信息
        使用方式：/查精灵 精灵名称
        """
        # 解析并校验指令参数
        message_parts = event.message_str.split(maxsplit=1)
        if len(message_parts) < 2:
            yield event.plain_result("⚠️ 指令参数缺失\n使用示例：/查精灵 谱尼")
            return
        
        pet_name = message_parts[1].strip()
        if not pet_name:
            yield event.plain_result("⚠️ 精灵名称不能为空\n使用示例：/查精灵 谱尼")
            return

        logger.info(f"开始查询精灵: {pet_name}")
        
        try:
            # API 调用统一包裹异常捕获，避免网络错误导致插件崩溃
            async with SeerAPI() as client:
                pet = await client.get_by_name('pet', pet_name)
            
            # 处理查询无结果的场景
            if not pet:
                yield event.plain_result(f"❌ 未查询到名为「{pet_name}」的精灵，请检查名称是否正确")
                return

            # 格式化回复内容，提升可读性
            reply = (
                f"🔍 精灵查询结果\n"
                f"精灵名称：{pet.name}\n"
                f"精灵ID：{pet.id}"
            )
            logger.info(f"精灵查询成功: {pet.name} (ID: {pet.id})")
            yield event.plain_result(reply)

        except Exception as e:
            error_detail = str(e)
            logger.error(f"精灵查询失败，名称: {pet_name}, 错误: {error_detail}")
            yield event.plain_result(f"❌ 查询出错，请稍后再试\n错误信息：{error_detail}")

    async def terminate(self) -> None:
        """插件卸载/停用时调用，执行资源清理"""
        logger.info("赛尔号精灵查询插件已卸载")