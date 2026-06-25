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
            # 每次请求新建客户端实例，避免连接复用导致的已关闭报错
            async with SeerAPI() as client:
                # 对应 GET /v1/pet/{name} 接口
                pet_detail = await client.get("pet", sprite_name)

                # ========== 基础信息 ==========
                info_text = "===== 赛尔号精灵图鉴 =====\n"
                info_text += f"名称：{getattr(pet_detail, 'name', '未知')}\n"
                info_text += f"精灵ID：{getattr(pet_detail, 'id', '未知')}\n"

                # 属性字段容错
                try:
                    attr_obj = getattr(pet_detail, 'type', None)
                    attr_name = getattr(attr_obj, 'name', str(attr_obj)) if attr_obj else "未知"
                except:
                    attr_name = "未知"
                info_text += f"属性：{attr_name}\n"

                # 性别字段容错
                try:
                    gender_obj = getattr(pet_detail, 'gender', None)
                    if not gender_obj:
                        gender_name = "无"
                    else:
                        gender_name = getattr(gender_obj, 'name', str(gender_obj))
                except:
                    gender_name = "无"
                info_text += f"性别：{gender_name}\n"

                # 进化阶段容错
                try:
                    evolve_idx = getattr(pet_detail, 'evolution_chain_index', 0)
                    evolve_stage = f"第{evolve_idx + 1}阶"
                except:
                    evolve_stage = "未知"
                info_text += f"进化阶段：{evolve_stage}\n\n"

                # ========== 种族值 ==========
                info_text += "【种族值】\n"
                try:
                    stats = getattr(pet_detail, 'base_stats', None)
                    if stats:
                        hp = getattr(stats, 'hp', 0)
                        atk = getattr(stats, 'atk', 0)
                        # 兼容 def 关键字字段
                        df = getattr(stats, 'def_', getattr(stats, 'def', 0))
                        sp_atk = getattr(stats, 'sp_atk', 0)
                        sp_def = getattr(stats, 'sp_def', 0)
                        spd = getattr(stats, 'spd', 0)
                        total = getattr(stats, 'total', hp + atk + df + sp_atk + sp_def + spd)

                        info_text += f"体力{hp:3d} 攻击{atk:3d} | 防御{df:3d}\n"
                        info_text += f"特攻{sp_atk:3d} 特防{sp_def:3d} | 速度{spd:3d}\n"
                        info_text += f"种族总和：{total}"
                    else:
                        info_text += "暂无种族值数据"
                except Exception:
                    info_text += "种族值数据解析失败"

                # ========== 魂印 ==========
                info_text += "\n\n【魂印】\n"
                try:
                    # 对应 GET /v1/soulmark/{name} 接口，传入精灵名称
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
                # 对应 GET /v1/mintmark/{name} 接口
                mintmark_detail = await client.get("mintmark", mintmark_name)

                # ========== 基础信息 ==========
                info_text = "===== 赛尔号刻印图鉴 =====\n"
                info_text += f"名称：{getattr(mintmark_detail, 'name', '未知')}\n"
                info_text += f"刻印ID：{getattr(mintmark_detail, 'id', '未知')}\n"

                # 刻印类型容错
                try:
                    type_obj = getattr(mintmark_detail, 'type', None)
                    type_name = getattr(type_obj, 'name', str(type_obj)) if type_obj else "未知"
                except:
                    type_name = "未知"
                info_text += f"类型：{type_name}\n\n"

                # ========== 刻印属性数值 ==========
                info_text += "【刻印属性】\n"
                hp = getattr(mintmark_detail, 'hp', 0)
                atk = getattr(mintmark_detail, 'atk', 0)
                # 兼容 def 关键字字段
                def_ = getattr(mintmark_detail, 'def_', getattr(mintmark_detail, 'def', 0))
                sp_atk = getattr(mintmark_detail, 'sp_atk', 0)
                sp_def = getattr(mintmark_detail, 'sp_def', 0)
                spd = getattr(mintmark_detail, 'spd', 0)
                total = hp + atk + def_ + sp_atk + sp_def + spd

                info_text += f"体力 +{hp}  攻击 +{atk} | 防御 +{def_}\n"
                info_text += f"特攻 +{sp_atk}  特防 +{sp_def} | 速度 +{spd}\n"
                info_text += f"属性总和：+{total}"

        except Exception as e:
            yield event.plain_result(f"查询失败：未找到刻印「{mintmark_name}」或接口异常 - {str(e)}")
            return

        yield event.plain_result(info_text)