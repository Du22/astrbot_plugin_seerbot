from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain
from seerapi import SeerAPI


class SeerSpriteQuery(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 移除全局客户端实例，改为每次请求独立创建

    @filter.command("精灵")
    async def query_sprite(self, event: AstrMessageEvent, sprite_name: str = ""):
        '''赛尔号精灵图鉴查询，示例：精灵 雷伊'''
        if not sprite_name:
            yield event.plain_result("格式错误！正确示例：精灵 雷伊")
            return

        try:
            # 每次查询新建客户端，上下文结束后自动销毁，避免连接关闭问题
            async with SeerAPI() as client:
                # 直接调用 GET /v1/pet/{name} 接口，通过名称一步获取精灵详情
                pet_detail = await client.get("pet", sprite_name, expand=True)

                # ========== 基础信息 ==========
                info_text = "===== 赛尔号精灵图鉴 =====\n"
                info_text += f"名称：{pet_detail.name}\n"
                info_text += f"精灵ID：{pet_detail.id}\n"

                # 属性：关联资源对象，expand 后可直接读取 name
                try:
                    attr_name = pet_detail.type.name
                except:
                    attr_name = f"类型ID:{pet_detail.type.id}"
                info_text += f"属性：{attr_name}\n"

                # 性别：关联资源对象，为空则显示“无”
                try:
                    gender_name = pet_detail.gender.name if pet_detail.gender else "无"
                except:
                    gender_name = "无"
                info_text += f"性别：{gender_name}\n"

                # 进化链索引（完整进化链需额外调用进化接口，当前仅返回阶段索引）
                info_text += f"进化阶段：第{pet_detail.evolution_chain_index + 1}阶\n\n"

                # ========== 种族值 ==========
                # 字段对齐官方 base_stats 结构，def 为 Python 关键字，必须用 getattr 访问
                stats = pet_detail.base_stats
                hp = stats.hp
                atk = stats.atk
                # 修复：用 getattr 替代 stats.def，避免语法错误
                df = stats.def_ if hasattr(stats, 'def_') else getattr(stats, 'def', 0)
                spatk = stats.sp_atk
                spdf = stats.sp_def
                speed = stats.spd
                total = stats.total  # 官方已内置总和字段，无需手动计算

                info_text += "【种族值】\n"
                info_text += f"体力{hp:3d} 攻击{atk:3d} | 防御{df:3d}\n"
                info_text += f"特攻{spatk:3d} 特防{spdf:3d} | 速度{speed:3d}\n"
                info_text += f"种族总和：{total}"

                # ========== 魂印 ==========
                info_text += "\n\n【魂印】\n"
                try:
                    # 调用官方 GET /v1/soulmark/{name} 接口，通过精灵名称获取魂印详情
                    soulmark_detail = await client.get("soulmark", sprite_name)
                    sm_name = getattr(soulmark_detail, 'name', "未知魂印")
                    sm_desc = getattr(soulmark_detail, 'description', "暂无效果描述")
                    info_text += f"名称：{sm_name}\n"
                    info_text += f"效果：{sm_desc}"
                except Exception:
                    # 接口报错（精灵无魂印、名称不匹配、404）时友好提示，不中断主查询
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
            # 每次查询新建客户端，上下文结束后自动销毁
            async with SeerAPI() as client:
                # 调用官方 GET /v1/mintmark/{name} 接口，通过名称获取刻印详情
                mintmark_detail = await client.get("mintmark", mintmark_name)

                # ========== 基础信息 ==========
                info_text = "===== 赛尔号刻印图鉴 =====\n"
                info_text += f"名称：{mintmark_detail.name}\n"
                info_text += f"刻印ID：{mintmark_detail.id}\n"

                # 刻印类型，兼容关联资源与纯文本两种返回
                try:
                    mint_type = mintmark_detail.type.name
                except:
                    mint_type = getattr(mintmark_detail, 'type', "未知类型")
                info_text += f"类型：{mint_type}\n\n"

                # ========== 刻印属性数值 ==========
                info_text += "【刻印属性】\n"
                # 字段命名与精灵种族值对齐，兼容 def 关键字
                hp = getattr(mintmark_detail, 'hp', 0)
                atk = getattr(mintmark_detail, 'atk', 0)
                def_ = getattr(mintmark_detail, 'def_', getattr(mintmark_detail, 'def', 0))
                sp_atk = getattr(mintmark_detail, 'sp_atk', 0)
                sp_def = getattr(mintmark_detail, 'sp_def', 0)
                spd = getattr(mintmark_detail, 'spd', 0)

                info_text += f"体力 +{hp}  攻击 +{atk} | 防御 +{def_}\n"
                info_text += f"特攻 +{sp_atk}  特防 +{sp_def} | 速度 +{spd}\n"
                
                # 计算属性加成总和
                total = hp + atk + def_ + sp_atk + sp_def + spd
                info_text += f"属性总和：+{total}"

        except Exception as e:
            yield event.plain_result(f"查询失败：未找到刻印「{mintmark_name}」或接口异常 - {str(e)}")
            return

        yield event.plain_result(info_text)