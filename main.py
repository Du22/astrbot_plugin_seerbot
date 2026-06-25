from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from seerapi import SeerAPI
from httpx import HTTPStatusError


class SeerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 精灵名称 -> ID 的本地缓存字典
        self._pet_name_map: dict[str, int] = {}
        self._map_loaded = False

    async def _load_pet_name_map(self):
        """加载全量精灵ID-名称映射到本地缓存（仅执行一次）"""
        if self._map_loaded:
            return
        try:
            async with SeerAPI() as client:
                # expand=False 仅拉取轻量引用，速度快流量小
                async for pet in client.list('pet', expand=False):
                    name = getattr(pet, 'name', '')
                    pet_id = getattr(pet, 'id', None)
                    if name and pet_id:
                        self._pet_name_map[name] = pet_id
            self._map_loaded = True
            logger.info(f"精灵名称索引加载完成，共 {len(self._pet_name_map)} 只精灵")
        except Exception as e:
            logger.error(f"加载精灵名称索引失败: {e}", exc_info=True)
            raise

    async def _get_pet_id_by_name(self, pet_name: str) -> int | None:
        """根据精灵名称查找ID，支持精确匹配"""
        await self._load_pet_name_map()
        # 精确匹配
        if pet_name in self._pet_name_map:
            return self._pet_name_map[pet_name]
        # 模糊匹配（包含）
        for name, pid in self._pet_name_map.items():
            if pet_name in name:
                return pid
        return None

    async def _get_pet_detail(self, pet_name: str):
        """
        根据精灵名称获取完整详情对象
        :return: (精灵详情对象, 匹配到的精灵名称)
        """
        pet_id = await self._get_pet_id_by_name(pet_name)
        if not pet_id:
            return None, pet_name
        
        async with SeerAPI() as client:
            pet = await client.get('pet', id=pet_id)
            return pet, getattr(pet, 'name', pet_name)

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

        try:
            pet, match_name = await self._get_pet_detail(message)
            if not pet:
                yield event.plain_result(f"未找到名为「{message}」的精灵，请检查名称是否正确")
                return
            
            reply = self._format_basic_and_race(pet)
            yield event.plain_result(reply)
        except HTTPStatusError as e:
            logger.error(f"SeerAPI HTTP错误: 状态码 {e.response.status_code}")
            yield event.plain_result(f"查询失败，API返回错误码 {e.response.status_code}")
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

        try:
            pet, match_name = await self._get_pet_detail(message)
            if not pet:
                yield event.plain_result(f"未找到名为「{message}」的精灵，请检查名称是否正确")
                return
            
            reply = self._format_soul_print(pet, match_name)
            yield event.plain_result(reply)
        except HTTPStatusError as e:
            logger.error(f"SeerAPI HTTP错误: 状态码 {e.response.status_code}")
            yield event.plain_result(f"查询失败，API返回错误码 {e.response.status_code}")
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

        try:
            pet, match_name = await self._get_pet_detail(message)
            if not pet:
                yield event.plain_result(f"未找到名为「{message}」的精灵，请检查名称是否正确")
                return
            
            reply = self._format_engraving(pet, match_name)
            yield event.plain_result(reply)
        except HTTPStatusError as e:
            logger.error(f"SeerAPI HTTP错误: 状态码 {e.response.status_code}")
            yield event.plain_result(f"查询失败，API返回错误码 {e.response.status_code}")
        except Exception as e:
            logger.error(f"刻印查询异常: {e}", exc_info=True)
            yield event.plain_result(f"查询出错：{str(e)}")

    def _format_basic_and_race(self, pet) -> str:
        """格式化：基础信息 + 种族值"""
        lines = []
        lines.append("=== 📖 精灵基础信息 ===")
        lines.append(f"精灵ID：{getattr(pet, 'id', '未知')}")
        lines.append(f"精灵名称：{getattr(pet, 'name', '未知')}")

        # 属性字段兼容
        element = getattr(pet, 'element', None) or getattr(pet, 'type', '未知')
        if isinstance(element, list):
            element = '·'.join(element)
        lines.append(f"精灵属性：{element}")

        gender = getattr(pet, 'gender', '未知')
        lines.append(f"性别：{gender}")
        lines.append("")

        lines.append("=== ⚔️ 种族值 ===")
        # 种族值兼容：直接字段 / 嵌套对象
        hp = getattr(pet, 'hp', '-')
        atk = getattr(pet, 'atk', '-')
        def_ = getattr(pet, 'def', '-')
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

    def _format_soul_print(self, pet, pet_name: str) -> str:
        """格式化：专属魂印（从精灵对象提取）"""
        lines = []
        lines.append(f"=== 💠 {pet_name} · 专属魂印 ===")

        # 多字段兼容
        soul_print = (
            getattr(pet, 'soul_print', None)
            or getattr(pet, 'soul_seal', None)
            or getattr(pet, 'soulmark', None)
            or getattr(pet, 'feature', None)
        )

        if soul_print:
            soul_name = getattr(soul_print, 'name', getattr(soul_print, 'title', '专属特性'))
            lines.append(f"魂印名称：{soul_name}")
            # 效果字段兼容
            effect = (
                getattr(soul_print, 'effect', None)
                or getattr(soul_print, 'description', None)
                or getattr(soul_print, 'soulmark_effect', None)
                or '暂无描述'
            )
            lines.append(f"效果：{effect}")
        else:
            # 尝试直接挂在精灵对象上的文本
            direct_effect = getattr(pet, 'soul_print_effect', None) or getattr(pet, 'feature_desc', None)
            if direct_effect:
                lines.append(direct_effect)
            else:
                lines.append("该精灵暂无专属魂印数据")

        return '\n'.join(lines)

    def _format_engraving(self, pet, pet_name: str) -> str:
        """格式化：专属刻印数值（从精灵对象提取）"""
        lines = []
        lines.append(f"=== 🎖️ {pet_name} · 专属刻印 ===")

        # 多字段兼容
        engravings = (
            getattr(pet, 'engravings', None)
            or getattr(pet, 'stamps', None)
            or getattr(pet, 'seals', None)
            or getattr(pet, 'mintmark', None)
            or getattr(pet, 'exclusive_engraving', None)
        )

        stat_map = {
            'hp': '体力', 'atk': '攻击', 'def': '防御',
            'spatk': '特攻', 'spdef': '特防', 'spd': '速度'
        }

        if engravings and isinstance(engravings, list) and len(engravings) > 0:
            for i, eng in enumerate(engravings[:3], 1):
                eng_name = getattr(eng, 'name', f'专属刻印{i}')
                lines.append(f"【{eng_name}】")

                has_stat = False
                for stat_key, stat_name in stat_map.items():
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
        self._pet_name_map.clear()
        self._map_loaded = False