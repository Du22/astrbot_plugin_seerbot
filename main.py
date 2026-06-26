from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star
from astrbot.api import logger
import aiohttp
from urllib.parse import quote
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
            # 直接请求官方接口，替代第三方 SeerAPI 库
            async with aiohttp.ClientSession() as session:
                # 对精灵名做 URL 编码，兼容中文/特殊字符
                url = f"https://api.seerapi.com/v1/pet/{quote(pet_name)}"
                async with session.get(url) as resp:
                    # 校验 HTTP 状态码
                    if resp.status != 200:
                        yield event.plain_result(f"❌ 请求失败，HTTP 状态码：{resp.status}")
                        return
                    # 解析 JSON 响应
                    result = await resp.json()
            
            logger.info(f"API 原始返回: {result}")

            # 校验接口业务状态码
            code = result.get("code", -1)
            if code not in (0, 200):
                err_msg = result.get("msg", "接口返回未知错误")
                yield event.plain_result(f"❌ 查询失败：{err_msg}")
                return

            # 安全获取 data 字段，彻底避免 KeyError 崩溃
            pet_data = result.get("data")
            if not pet_data:
                yield event.plain_result("❌ 未找到该精灵，请检查名称是否正确（需精确全名）")
                return

            # 读取精灵基础信息
            name = pet_data.get("name", "未知")
            pet_id = pet_data.get("id", "未知")
            
            reply = (
                f"✅ 精灵查询结果\n"
                f"精灵名称: {name}\n"
                f"精灵ID: {pet_id}"
            )
            yield event.plain_result(reply)

        except aiohttp.ClientError as e:
            logger.error(f"网络请求错误: {e}")
            yield event.plain_result("❌ 网络异常，无法连接精灵查询接口")
        except Exception as e:
            logger.error(f"查询精灵发生错误: {type(e).__name__}: {e}", exc_info=True)
            yield event.plain_result(f"❌ 查询出错：{str(e)}\n请查看控制台日志排查详情")

    async def terminate(self):
        '''插件卸载时调用'''
        pass