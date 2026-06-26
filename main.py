from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star
from astrbot.api import logger # 使用 astrbot 提供的 logger 接口
from seerapi import SeerAPI
import asyncio

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("查精灵")
    async def main(self, event: AstrMessageEvent):
        '''这是一个赛尔号指令''' # 这是 handler 的描述，将会被解析方便用户了解插件内容。非常建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str.split(maxsplit=1) # 获取消息的纯文本内容
        if len(message_str) < 2 or not message_str[1].strip():
            yield event.plain_result("⚠️ 指令参数缺失\n使用示例：/查精灵 谱尼")
            return
        pet_name =message_str[1].strip()
        logger.info(f"开始查询精灵: {pet_name}")
        try:
            # 若 SeerAPI 不支持 async with，请改为 client = SeerAPI() 后手动调用
            async with SeerAPI() as client:
                pet = await client.get_by_name('pet', pet_name)
            
            # 空值判断：处理查询不到精灵的情况
            if not pet:
                yield event.plain_result(f"❌ 未查询到名为「{pet_name}」的精灵，请检查名称是否正确")
                return

            # 构造返回消息
            reply = (
                f"✅ 精灵查询结果\n"
                f"精灵名称: {pet.name}\n"
                f"精灵ID: {pet.id}"
            )
            yield event.plain_result(reply)

        except Exception as e:
            logger.error(f"查询精灵失败: {str(e)}")
            yield event.plain_result(f"❌ 查询失败，接口异常，请稍后重试") # 发送一条纯文本消息
    
    

    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''