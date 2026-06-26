from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star
from astrbot.api import logger
from seerapi import SeerAPI
import asyncio

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("查精灵")
    async def main(self, event: AstrMessageEvent):
        '''赛尔号精灵查询指令'''
        message_str = event.message_str.split(maxsplit=1)
        if len(message_str) < 2 or not message_str[1].strip():
            yield event.plain_result("⚠️ 指令参数缺失\n使用示例：/查精灵 谱尼")
            return
        
        pet_name = message_str[1].strip()
        logger.info(f"开始查询精灵: {pet_name}")

        try:
            # 若 async with 报错，可注释本段，改用下方同步调用写法
            async with SeerAPI() as client:
                pet = await client.get_by_name('skill', pet_name)
            
            # 调试日志：确认API返回的原始结构与类型，方便排查
            logger.info(f"API返回原始数据: {pet}")
            logger.info(f"返回数据类型: {type(pet)}")

            # 兼容字典和对象两种返回格式
            if isinstance(pet, dict):
                pet_data = pet.get('data', pet)
                name = pet_data.get('name', '未知')
                pet_id = pet_data.get('power', '未知')
            else:
                name = getattr(pet, 'name', '未知')
                pet_id = getattr(pet, 'power', '未知')
            
            reply = (
                f"✅ 精灵查询结果\n"
                f"精灵名称: {name}\n"
                f"精灵ID: {pet_id}"
            )
            yield event.plain_result(reply)

        except KeyError as e:
            logger.error(f"API返回结构异常，缺失键: {e}")
            yield event.plain_result("❌ 查询失败：未找到该精灵，请检查名称是否正确")
        except Exception as e:
            logger.error(f"查询精灵发生错误: {type(e).__name__}: {e}", exc_info=True)
            yield event.plain_result(f"❌ 查询出错：{str(e)}\n请查看控制台日志排查详情")

    async def terminate(self):
        '''插件卸载时调用'''
        pass