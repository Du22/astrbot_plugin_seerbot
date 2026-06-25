from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from seerapi import SeerAPI
from httpx import HTTPStatusError


class SeerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 复用客户端实例，利用内置缓存提升速度
        self._client = None

    async def _get_client(self) -> SeerAPI:
        """获取或初始化 SeerAPI 客户端"""
        if self._client is None:
            self._client = SeerAPI()
        return self._client

    async def _get_pet_by_name(self, pet_name: str):
        """
        公共方法：根据精灵名称获取精灵详情对象
        :param pet_name: 精灵名称
        :return: 精灵详情对象，未找到返回 None
        """
        client = await self._get_client()
        
        # 按名称搜索
        result = await client.get_by_name('pet', pet_name)
        if not result.data:
            return None
        
        # 取第一个匹配结果，用关键字参数 id= 获取详情
        pet_id = list(result.data.keys())[0]
        pet = await client.get('pet', id=pet_id)
        return pet

    @filter.command("精灵")
    async def query_pet(self, event: AstrMessageEvent):
        '''
        查询赛尔号精灵基础信息与种族值
        用法：/精灵 精灵名称
        示例：/精灵 谱尼
        '''
        message = event.message_str.strip()
        if not message:
            yield event.plain_result("请输入精灵名称，例如：/精灵 谱尼")
            return

        pet_name = message.strip()
        try:
            pet = await self._get_pet_by_name(pet_name)
            if not pet:
                yield event.plain_result(f"未找到名为「{pet_name}」的精灵，请检查名称是否正确")
                return

            reply = self._format_basic_and_race(pet)
            yield event.plain_result(reply)

        except HTTPStatusError as e:
            logger.error(f"SeerAPI HTTP错误: 状态码 {e.response.status_code}, 响应: {e.response.text}")
            yield event.plain_result(f"查询失败，API返回错误码 {e.response.status_code}，请稍后再试")
        except Exception as e:
            logger.error(f"精灵查询异常: {e}", exc_info=True)
            yield event.plain_result(f"查询出错：{str(e)}")

    @filter.command("魂印")
    async def query_soul_print(self, event: AstrMessageEvent):
        '''
        查询赛尔号精灵专属魂印
        用法：/魂印 精灵名称
        示例：/魂印 谱尼
        '''
        message = event.message_str.strip()
        if not message:
            yield event.plain_result("请输入精灵名称，例如：/魂印 谱尼")
            return

        pet_name = message.strip()
        try:
            pet = await self._get_pet_by_name(pet_name)
            if not pet:
                yield event.plain_result(f"未找到名为「{pet_name}」的精灵，请检查名称是否正确")
                return

            reply = self._format_soul_print(pet)
            yield event.plain_result(reply)

        except HTTPStatusError as e:
            logger.error(f"SeerAPI HTTP错误: 状态码 {e.response.status_code}, 响应: {e.response.text}")
            yield event.plain_result(f"查询失败，API返回错误码 {e.response.status_code}，请稍后再试")
        except Exception as e:
            logger.error(f"魂印查询异常: {e}", exc_info=True)
            yield event.plain_result(f"查询出错：{str(e)}")

    @filter.command("刻印")
    async def query_engraving(self, event: AstrMessageEvent):
        '''
        查询赛尔号精灵专属刻印数值
        用法：/刻印 精灵名称
        示例：/刻印 谱尼
        '''
        message = event.message_str.strip()
        if not message:
            yield event.plain_result("请输入精灵名称，例如：/刻印 谱尼")
            return

        pet_name = message.strip()
        try:
            pet = await self._get_pet_by_name(pet_name)
            if not pet:
                yield event.plain_result(f"未找到名为「{pet_name}」的精灵，请检查名称是否正确")
                return

            reply = self._format_engraving(pet)
            yield event.plain_result(reply)

        except HTTPStatusError as e:
            logger.error(f"SeerAPI HTTP错误: 状态码 {e.response.status_code}, 响应: {e.response.text}")
            yield event.plain_result(f"查询失败，API返回错误码 {e.response.status_code}，请稍后再试")
        except Exception as e:
            logger.error(f"刻印查询异常: {e}", exc_info=True)
            yield event.plain_result(f"查询出错：{str(e)}")

    def _format_basic_and_race(self, pet) -> str:
        """格式化：基础信息 + 种族值"""
        lines = []
        lines.append("=== 📖 精灵基础信息 ===")
        lines.append(f"精灵ID：{getattr(pet, 'id', '未知')}")
        lines.append(f"精灵名称：{getattr(pet, 'name', '未知')}")

        # 属性兼容：element / type
        element = getattr(pet, 'element', None) or getattr(pet, 'type', '未知')
        if isinstance(element, list):
            element = '·'.join(element)
        lines.append(f"精灵属性：{element}")

        gender = getattr(pet, 'gender', '未知')
        lines.append(f"性别：{gender}")
        lines.append("")

        lines.append("=== ⚔️ 种族值 ===")
        # 种族值兼容字段：base_stats / race_value / 直接挂在对象上
        stats = getattr(pet, 'base_stats', None) or getattr(pet, 'race_value', None)

        if stats:
            hp = getattr(stats, 'hp', getattr(stats, '体力', '-'))
            atk = getattr(stats, 'atk', getattr(stats, '攻击', '-'))
            def_ = getattr(stats, 'def_', getattr(stats, '防御', '-'))
            spatk = getattr(stats, 'spatk', getattr(stats, '特攻', '-'))
            spdef = getattr(stats, 'spdef', getattr(stats, '特防', '-'))
            spd = getattr(stats, 'spd', getattr(stats, '速度', '-'))

            lines.append(f"体力：{hp}")
            lines.append(f"攻击：{atk}")
            lines.append(f"防御：{def_}")
            lines.append(f"特攻：{spatk}")
            lines.append(f"特防：{spdef}")
            lines.append(f"速度：{spd}")

            # 计算种族值总和
            try:
                total = sum(int(x) for x in [hp, atk, def_, spatk, spdef, spd] if str(x).isdigit())
                lines.append(f"总和：{total}")
            except:
                pass
        else:
            # 尝试直接从pet对象取字段
            hp = getattr(pet, 'hp', '-')
            atk = getattr(pet, 'atk', '-')
            def_ = getattr(pet, 'def_', '-')
            spatk = getattr(pet, 'spatk', '-')
            spdef = getattr(pet, 'spdef', '-')
            spd = getattr(pet, 'spd', '-')

            if hp != '-' or atk != '-':
                lines.append(f"体力：{hp}")
                lines.append(f"攻击：{atk}")
                lines.append(f"防御：{def_}")
                lines.append(f"特攻：{spatk}")
                lines.append(f"特防：{spdef}")
                lines.append(f"速度：{spd}")
            else:
                lines.append("暂无种族值数据")

        return '\n'.join(lines)

    def _format_soul_print(self, pet) -> str:
        """格式化：专属魂印"""
        lines = []
        pet_name = getattr(pet, 'name', '未知')
        lines.append(f"=== 💠 {pet_name} · 专属魂印 ===")

        # 魂印兼容字段：soul_print / soul_seal / feature
        soul_print = getattr(pet, 'soul_print', None) or getattr(pet, 'soul_seal', None) or getattr(pet, 'feature', None)

        if soul_print:
            soul_name = getattr(soul_print, 'name', getattr(soul_print, 'title', '专属特性'))
            lines.append(f"魂印名称：{soul_name}")
            # 效果兼容字段：effect / description / content
            soul_effect = getattr(soul_print, 'effect', getattr(soul_print, 'description', getattr(soul_print, 'effect_desc', '暂无描述')))
            lines.append(f"效果：{soul_effect}")
        else:
            # 尝试直接从pet对象取魂印效果文本
            soul_effect = getattr(pet, 'soul_print_effect', None) or getattr(pet, 'feature_desc', None)
            if soul_effect:
                lines.append(soul_effect)
            else:
                lines.append("该精灵暂无专属魂印")

        return '\n'.join(lines)

    def _format_engraving(self, pet) -> str:
        """格式化：专属刻印数值"""
        lines = []
        pet_name = getattr(pet, 'name', '未知')
        lines.append(f"=== 🎖️ {pet_name} · 专属刻印 ===")

        # 刻印兼容字段：engravings / stamps / seals / exclusive_engraving
        engravings = getattr(pet, 'engravings', None) or getattr(pet, 'stamps', None) or getattr(pet, 'seals', None) or getattr(pet, 'exclusive_engraving', None)

        if engravings and isinstance(engravings, list) and len(engravings) > 0:
            stat_name_map = {
                'hp': '体力', 'atk': '攻击', 'def_': '防御',
                'spatk': '特攻', 'spdef': '特防', 'spd': '速度'
            }

            for i, eng in enumerate(engravings[:3], 1):
                eng_name = getattr(eng, 'name', f'专属刻印{i}')
                lines.append(f"【{eng_name}】")

                has_stat = False
                for stat_key, stat_name in stat_name_map.items():
                    val = getattr(eng, stat_key, None)
                    if val and val != 0:
                        lines.append(f"  {stat_name}：+{val}")
                        has_stat = True

                if not has_stat:
                    lines.append("  暂无数值数据")
                lines.append("")
        else:
            lines.append("暂无专属刻印数据")

        return '\n'.join(lines)

    async def terminate(self):
        """插件卸载时关闭客户端连接"""
        if self._client:
            await self._client.aclose()
            self._client = None