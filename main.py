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
    async def query_elf(self, event: AstrMessageEvent):
        """查询精灵基础信息"""
        # 提取命令参数
        args = event.message_str.strip().split(maxsplit=1)
        if len(args) < 2:
            yield event.plain_result("⚠️ 请输入精灵名称\n示例：/精灵 谱尼")
            return

        elf_name = args[1].strip()
        try:
            async with SeerAPI() as client:
                result = await client.get_by_name('elf', elf_name)

                if not result or not result.data:
                    yield event.plain_result(f"❌ 未查询到名为「{elf_name}」的精灵")
                    return

                # 取第一个匹配结果
                elf_id, elf = next(iter(result.data.items()))

                # 排版优化
                reply = f"🔍 精灵查询结果\n"
                reply += "─────────────────\n"
                reply += f"📌 序号：{elf_id}\n"
                reply += f"📛 名称：{elf.name}\n"

                # 属性字段兼容
                elf_type = getattr(elf, 'element', getattr(elf, 'type', '未知'))
                reply += f"🎯 属性：{elf_type}\n"

                # 种族值提取与自动求和
                reply += "\n📊 种族值\n"
                hp = getattr(elf, 'hp', 0)
                atk = getattr(elf, 'attack', getattr(elf, 'atk', 0))
                defense = getattr(elf, 'defense', getattr(elf, 'def', 0))
                sp_atk = getattr(elf, 'special_attack', getattr(elf, 'sp_atk', 0))
                sp_def = getattr(elf, 'special_defense', getattr(elf, 'sp_def', 0))
                speed = getattr(elf, 'speed', 0)

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
            yield event.plain_result(f"⚠️ 查询出错：{str(e)}")

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

                if not result or not result.data:
                    yield event.plain_result(f"❌ 未查询到名为「{skill_name}」的技能")
                    return

                count = len(result.data)
                reply = f"🔮 技能查询：{skill_name}\n"
                reply += f"共找到 {count} 个同名技能\n"

                for idx, (skill_id, skill) in enumerate(result.data.items(), 1):
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
            yield event.plain_result(f"⚠️ 查询出错：{str(e)}")

    async def terminate(self):
        """插件卸载时调用，可选"""
        pass