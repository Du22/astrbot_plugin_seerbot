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
    async def seerpet(self, event: AstrMessageEvent):
        '''这是一个赛尔号指令''' # 这是 handler 的描述，将会被解析方便用户了解插件内容。非常建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str.split(maxsplit=1) # 获取消息的纯文本内容
        if len(message_str) < 2 or not message_str[1].strip():
            yield event.plain_result("⚠️ 指令参数缺失\n使用示例：/查精灵 谱尼")
            return
        pet_name =message_str[1].strip()
        async def main(self):
         async with SeerAPI() as client:
        # 查询技能数据
          pet = await client.get_by_name('pet', pet_name)
          print(f"精灵名称: {pet.name}")
          print(f"精灵ID: {pet.id}")
    
   
         logger.info("开始调取api") # 记录日志，方便调试

         yield event.plain_result(f"精灵名称: {pet.name}\n精灵ID: {pet.id}") # 发送一条纯文本消息
    
    

    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''