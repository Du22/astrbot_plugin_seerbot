"""
AstrBot 赛尔号精灵查询插件
适配 AstrBot v3 Star 架构
基于 SeerAPI 实现精灵基础信息与技能效果查询
"""
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from seerapi import SeerAPI


class SeerQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("精灵", aliases=["seer", "赛尔号精灵"])
    async def query_pet(self, event: AstrMessageEvent):
        """查询精灵基础信息"""
        args = event.message_str.strip().split(maxsplit=1)
        if len(args) < 2:
            yield event.plain_result("⚠️ 请输入精灵名称\n示例：/精灵 谱尼")
            return

        pet_name = args[1].strip()
        try:
            async with SeerAPI() as client:
                result = await client.get_by_name('pet', pet_name)

                # ========== 核心修复：安全兼容 data 属性 ==========
                if hasattr(result, 'data'):
                    data = result.data
                else:
                    # 如果没有data属性，直接把result本身当数据字典
                    data = result

                if not data:
                    yield event.plain_result(f"❌ 未查询到名为「{pet_name}」的精灵")
                    return
                # ==================================================

                # 取第一个匹配结果
                pet_id, pet = next(iter(data.items()))

                # 排版优化
                reply = f"🔍 精灵查询结果\n"
                reply += "─────────────────\n"
                reply += f"📌 序号：{pet_id}\n"
                reply += f"📛 名称：{pet.name}\n"

                # 属性字段兼容
                pet_type = getattr(pet, 'element', getattr(pet, 'type', '未知'))
                reply += f"🎯 属性：{pet_type}\n"

                # 种族值提取与自动求和
                reply += "\n📊 种族值\n"
                hp = getattr(pet, 'hp', 0)
                atk = getattr(pet, 'attack', getattr(pet, 'atk', 0))
                defense = getattr(pet, 'defense', getattr(pet, 'def', 0))
                sp_atk = getattr(pet, 'special_attack', getattr(pet, 'sp_atk', 0))
                sp_def = getattr(pet, 'special_defense', getattr(pet, 'sp_def', 0))
                speed = getattr(pet, 'speed', 0)

                reply += f"  体力：{hp}\n"
                reply += f"  攻击：{atk}\n"
                reply += f"  防御：{defense}\n"
                reply += f"  特攻：{sp_atk}\n"
                reply += f"  特防：{sp_def}\n"
                reply += f"  速度：{speed}\n"

                try:
                    total = sum(map(int, [hp, atk, defense, sp_atk, sp_def, speed]))
                    if total > 0:
                        reply += f"  ──────\n  总和：{total}\n"
                except (ValueError, TypeError):
                    pass

                yield event.plain_result(reply)

        except Exception as e:
            # 输出详细错误类型，方便排查
            err_info = f"{type(e).__name__}: {str(e)}"
            yield event.plain_result(f"⚠️ 查询出错：{err_info}")

    @filter.command("技能", aliases=["skill", "赛尔号技能"])
    async def query_skill(self, event: AstrMessageEvent):
        """查询技能详细效果"""
        args = event.message_str.strip().split(maxsplit=1)
        if len(args) < 2:
            yield event.plain_result("⚠️ 请输入技能名称\n示例：/技能 虚妄幻境")
            return

        skill_name = args[1].strip()
        try:
            async with SeerAPI() as client:
                result = await client.get_by_name('skill', skill_name)

                # 同步加固兼容
                if hasattr(result, 'data'):
                    data = result.data
                else:
                    data = result

                if not data:
                    yield event.plain_result(f"❌ 未查询到名为「{skill_name}」的技能")
                    return

                count = len(data)
                reply = f"🔮 技能查询：{skill_name}\n"
                reply += f"共找到 {count} 个同名技能\n"

                for idx, (skill_id, skill) in enumerate(data.items(), 1):
                    reply += "\n─────────────────\n"
                    reply += f"【第 {idx} 个】ID: {skill_id}\n"

                    # 技能基础信息兼容
                    if hasattr(skill, 'skill_name'):
                        reply += f"名称：{skill.skill_name}\n"
                    skill_type = getattr(skill, 'skill_type', getattr(skill, 'type', '-'))
                    reply += f"类型：{skill_type}\n"

                    power = getattr(skill, 'power', '-')
                    pp = getattr(skill, 'pp', '-')
                    reply += f"威力：{power} | PP：{pp}\n"

                    # 核心技能效果
                    if hasattr(skill, 'skill_effect') and skill.skill_effect:
                        reply += f"\n✨ 效果：\n{skill.skill_effect}\n"

                # QQ单条消息长度保护
                if len(reply) > 3800:
                    reply = reply[:3800] + "\n\n...内容过长已截断"

                yield event.plain_result(reply)

        except Exception as e:
            err_info = f"{type(e).__name__}: {str(e)}"
            yield event.plain_result(f"⚠️ 查询出错：{err_info}")

    async def terminate(self):
        """插件卸载时调用，可选"""
        pass