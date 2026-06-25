from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain
from seerapi import SeerAPI


class SeerSpriteQuery(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("精灵")
    async def query_sprite(self, event: AstrMessageEvent, sprite_name: str = ""):
        '''赛尔号精灵图鉴查询，示例：精灵 雷伊'''
        if not sprite_name:
            yield event.plain_result("格式错误！正确示例：精灵 雷伊")
            return

        try:
            async with SeerAPI() as client:
                # 移除不支持的 expand 参数，按 SDK 原生签名调用接口
                pet_detail = await client.get("pet", sprite_name)

                # ========== 基础信息 ==========
                info_text = "===== 赛尔号精灵图鉴 =====\n"
                info_text += f"名称：{pet_detail.name}\n"
                info_text += f"精灵ID：{pet_detail.id}\n"

                # 属性：兼容关联资源对象与纯ID两种返回
                try:
                    attr_type = pet_detail.type
                    attr_name = attr_type.name if hasattr(attr_type, 'name') else str(attr_type)
                except:
                    attr_name = "未知"
                info_text += f"属性：{attr_name}\n"

                # 性别：兼容空值、关联对象、纯ID三种情况
                try:
                    gender = pet_detail.gender
                    if not gender:
                        gender_name = "无"
                    else:
                        gender_name = gender.name if hasattr(gender, 'name') else str(gender)
                except:
                    gender_name = "无"
                info_text += f"性别：{gender_name}\n"

                # 进化阶段
                try:
                    evolve_stage = pet_detail.evolution_chain_index + 1
                except:
                    evolve_stage = "未知"
                info_text += f"进化阶段：第{evolve_stage}阶\n\n"

                # ========== 种族值 ==========
                stats = pet_detail.base_stats
                hp = getattr(stats, 'hp', 0)
                atk = getattr(stats, 'atk', 0)
                df = getattr(stats, 'def_', getattr(stats, 'def', 0))
                spatk = getattr(stats, 'sp_atk', 0)
                spdf = getattr(stats, 'sp_def', 0)
                speed = getattr(stats, 'spd', 0)
                total = getattr(stats, 'total', hp + atk + df + spatk + spdf + speed)

                info_text += "【种族值】\n"
                info_text += f"体力{hp:3d} 攻击{atk:3d} | 防御{df:3d}\n"
                info_text += f"特攻{spatk:3d} 特防{spdf:3d} | 速度{speed:3d}\n"
                info_text += f"种族总和：{total}"

                # ========== 魂印 ==========
                info_text += "\n\n【魂印】\n"
                try:
                    soulmark_detail = await client.get("soulmark", sprite_name)
                    sm_name = getattr(soulmark_detail, 'name', "未知魂印")
                    sm_desc = getattr(soulmark_detail, 'description', "暂无效果描述")
                    info_text += f"名称：{sm_name}\n"
                    info_text += f"效果：{sm_desc}"
                except Exception:
                    info_text += "该精灵无魂印"

        except Exception as e:
            yield event.plain_result(f"查询失败：未找到精灵「{sprite_name}」或接口异常 - {str(e)}")
            return

        yield event.plain_result(info_text)

    @filter.command("刻印")
    async def query_mintmark(self, event: AstrMessageEvent, mintmark_name: str = ""):
        '''赛尔号刻印属性查询，示例：刻印 衡·巨刃'''
        if not mintmark_name:
            yield event.plain_result("格式错误！正确示例：刻印 衡·巨刃")
            return

        try:
            async with SeerAPI() as client:
                mintmark_detail = await client.get("mintmark", mintmark_name)

                # ========== 基础信息 ==========
                info_text = "===== 赛尔号刻印图鉴 =====\n"
                info_text += f"名称：{mintmark_detail.name}\n"
                info_text += f"刻印ID：{mintmark_detail.id}\n"

                # 刻印类型兼容处理
                try:
                    mint_type = mintmark_detail.type
                    mint_type_name = mint_type.name if hasattr(mint_type, 'name') else str(mint_type)
                except:
                    mint_type_name = "未知类型"
                info_text += f"类型：{mint_type_name}\n\n"

                # ========== 刻印属性数值 ==========
                info_text += "【刻印属性】\n"
                hp = getattr(mintmark_detail, 'hp', 0)
                atk = getattr(mintmark_detail, 'atk', 0)
                def_ = getattr(mintmark_detail, 'def_', getattr(mintmark_detail, 'def', 0))
                sp_atk = getattr(mintmark_detail, 'sp_atk', 0)
                sp_def = getattr(mintmark_detail, 'sp_def', 0)
                spd = getattr(mintmark_detail, 'spd', 0)

                info_text += f"体力 +{hp}  攻击 +{atk} | 防御 +{def_}\n"
                info_text += f"特攻 +{sp_atk}  特防 +{sp_def} | 速度 +{spd}\n"
                
                total = hp + atk + def_ + sp_atk + sp_def + spd
                info_text += f"属性总和：+{total}"

        except Exception as e:
            yield event.plain_result(f"查询失败：未找到刻印「{mintmark_name}」或接口异常 - {str(e)}")
            return

        yield event.plain_result(info_text)