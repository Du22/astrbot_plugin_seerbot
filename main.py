from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from seerapi import SeerAPI
from httpx import HTTPStatusError


class SeerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

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
            async with SeerAPI() as client:
                result = await client.get_by_name('pet', pet_name)
                if not result.data:
                    yield event.plain_result(f"未找到名为「{pet_name}」的精灵，请检查名称是否正确")
                    return

                # 取第一个匹配结果
                pet_id = list(result.data.keys())[0]
                pet = result.data[pet_id]
                reply = self._format_pet_info(pet)
                yield event.plain_result(reply)

        except HTTPStatusError as e:
            logger.error(f"SeerAPI HTTP错误: 状态码 {e.response.status_code}, 响应: {e.response.text}")
            yield event.plain_result(f"查询失败，API返回错误码 {e.response.status_code}，请稍后再试")
        except Exception as e:
            logger.error(f"精灵查询异常: {e}", exc_info=True)
            yield event.plain_result(f"查询出错：{str(e)}")

    @filter.command("魂印")
    async def query_soulmark(self, event: AstrMessageEvent):
        '''
        查询赛尔号精灵专属魂印
        用法：/魂印 精灵名称
        示例：/魂印 谱尼
        '''
        message = event.message_str.strip()
        if not message:
            yield event.plain_result("请输入精灵名称，例如：/魂印 谱尼")
            return

        name = message.strip()
        try:
            async with SeerAPI() as client:
                result = await client.get_by_name('soulmark', name)
                if not result.data:
                    yield event.plain_result(f"未找到「{name}」对应的魂印信息，请检查名称是否正确")
                    return

                # 取第一个匹配结果
                soulmark_id = list(result.data.keys())[0]
                soulmark = result.data[soulmark_id]
                reply = self._format_soulmark(soulmark)
                yield event.plain_result(reply)

        except HTTPStatusError as e:
            logger.error(f"SeerAPI HTTP错误: 状态码 {e.response.status_code}, 响应: {e.response.text}")
            yield event.plain_result(f"查询失败，API返回错误码 {e.response.status_code}，请稍后再试")
        except Exception as e:
            logger.error(f"魂印查询异常: {e}", exc_info=True)
            yield event.plain_result(f"查询出错：{str(e)}")

    @filter.command("刻印")
    async def query_mintmark(self, event: AstrMessageEvent):
        '''
        查询赛尔号精灵专属刻印数值
        用法：/刻印 精灵名称
        示例：/刻印 谱尼
        '''
        message = event.message_str.strip()
        if not message:
            yield event.plain_result("请输入精灵名称，例如：/刻印 谱尼")
            return

        name = message.strip()
        try:
            async with SeerAPI() as client:
                result = await client.get_by_name('mintmark', name)
                if not result.data:
                    yield event.plain_result(f"未找到「{name}」对应的刻印信息，请检查名称是否正确")
                    return

                reply = self._format_mintmark(result.data, name)
                yield event.plain_result(reply)

        except HTTPStatusError as e:
            logger.error(f"SeerAPI HTTP错误: 状态码 {e.response.status_code}, 响应: {e.response.text}")
            yield event.plain_result(f"查询失败，API返回错误码 {e.response.status_code}，请稍后再试")
        except Exception as e:
            logger.error(f"刻印查询异常: {e}", exc_info=True)
            yield event.plain_result(f"查询出错：{str(e)}")

    def _format_pet_info(self, pet) -> str:
        """格式化精灵基础信息+种族值"""
        lines = []
        lines.append("=== 📖 精灵基础信息 ===")
        lines.append(f"精灵ID：{getattr(pet, 'id', '未知')}")
        lines.append(f"精灵名称：{getattr(pet, 'name', getattr(pet, 'pet_name', '未知'))}")

        # 属性字段兼容
        element = getattr(pet, 'element', None) or getattr(pet, 'type', getattr(pet, 'pet_type', '未知'))
        if isinstance(element, list):
            element = '·'.join(element)
        lines.append(f"精灵属性：{element}")

        gender = getattr(pet, 'gender', getattr(pet, 'pet_gender', '未知'))
        lines.append(f"性别：{gender}")
        lines.append("")

        lines.append("=== ⚔️ 种族值 ===")
        # 优先直接字段，兼容前缀命名和嵌套对象
        hp = getattr(pet, 'hp', getattr(pet, 'pet_hp', '-'))
        atk = getattr(pet, 'atk', getattr(pet, 'pet_atk', '-'))
        def_ = getattr(pet, 'def', getattr(pet, 'pet_def', '-'))
        spatk = getattr(pet, 'spatk', getattr(pet, 'pet_spatk', '-'))
        spdef = getattr(pet, 'spdef', getattr(pet, 'pet_spdef', '-'))
        spd = getattr(pet, 'spd', getattr(pet, 'pet_spd', '-'))

        if hp != '-' or atk != '-':
            lines.append(f"体力：{hp}")
            lines.append(f"攻击：{atk}")
            lines.append(f"防御：{def_}")
            lines.append(f"特攻：{spatk}")
            lines.append(f"特防：{spdef}")
            lines.append(f"速度：{spd}")
            try:
                total = sum(int(x) for x in [hp, atk, def_, spatk, spdef, spd] if str(x).isdigit())
                lines.append(f"总和：{total}")
            except:
                pass
        else:
            # 兼容嵌套种族值对象
            stats = getattr(pet, 'base_stats', None) or getattr(pet, 'race_value', None)
            if stats:
                hp = getattr(stats, 'hp', '-')
                atk = getattr(stats, 'atk', '-')
                def_ = getattr(stats, 'def', '-')
                spatk = getattr(stats, 'spatk', '-')
                spdef = getattr(stats, 'spdef', '-')
                spd = getattr(stats, 'spd', '-')
                lines.append(f"体力：{hp}")
                lines.append(f"攻击：{atk}")
                lines.append(f"防御：{def_}")
                lines.append(f"特攻：{spatk}")
                lines.append(f"特防：{spdef}")
                lines.append(f"速度：{spd}")
                try:
                    total = sum(int(x) for x in [hp, atk, def_, spatk, spdef, spd] if str(x).isdigit())
                    lines.append(f"总和：{total}")
                except:
                    pass
            else:
                lines.append("暂无种族值数据")

        return '\n'.join(lines)

    def _format_soulmark(self, soulmark) -> str:
        """格式化魂印信息，参考 skill_effect 命名规则"""
        lines = []
        lines.append("=== 💠 专属魂印 ===")

        name = getattr(soulmark, 'name', getattr(soulmark, 'soulmark_name', '专属特性'))
        lines.append(f"魂印名称：{name}")

        # 优先前缀命名（对齐 skill_effect 风格），再兼容通用字段
        effect = getattr(soulmark, 'soulmark_effect', None)
        if not effect:
            effect = getattr(soulmark, 'effect', getattr(soulmark, 'description', '暂无描述'))
        lines.append(f"效果：{effect}")

        return '\n'.join(lines)

    def _format_mintmark(self, data: dict, query_name: str) -> str:
        """格式化刻印数值，支持多刻印结果"""
        lines = []
        lines.append(f"=== 🎖️ {query_name} · 专属刻印 ===")

        stat_map = {
            'hp': '体力', 'atk': '攻击', 'def': '防御',
            'spatk': '特攻', 'spdef': '特防', 'spd': '速度'
        }

        for idx, (mid, mintmark) in enumerate(data.items(), 1):
            eng_name = getattr(mintmark, 'name', getattr(mintmark, 'mintmark_name', f'专属刻印{idx}'))
            lines.append(f"【{eng_name}】")

            has_stat = False
            for stat_key, stat_name in stat_map.items():
                # 优先前缀字段，再兼容直接字段
                val = getattr(mintmark, f'mintmark_{stat_key}', None)
                if val is None:
                    val = getattr(mintmark, stat_key, None)
                if val and val != 0:
                    lines.append(f"  {stat_name}：+{val}")
                    has_stat = True

            if not has_stat:
                lines.append("  暂无数值数据")
            lines.append("")

        return '\n'.join(lines)

    async def terminate(self):
        pass