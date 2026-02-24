"""
AI商品文案生成Agent
使用大语言模型生成优化的商品信息
"""

import json
import re
from typing import Dict, List, Optional


class ProductAgent:
    """商品AI生成Agent"""
    
    def __init__(self):
        self.style_presets = {
            "ins风": {"tone": "清新文艺", "keywords": ["简约", "质感", "lifestyle"]},
            "可爱风": {"tone": "萌系甜美", "keywords": ["可爱", "少女心", "萌"]},
            "商务风": {"tone": "专业品质", "keywords": ["品质", "商务", "高端"]},
            "性价比风": {"tone": "实惠超值", "keywords": ["超值", "爆款", "性价比"]},
            "极简风": {"tone": "简洁纯粹", "keywords": ["极简", "纯粹", "设计感"]},
            "复古风": {"tone": "怀旧经典", "keywords": ["复古", "经典", "怀旧"]},
        }
    
    def parse_input(self, user_input: str) -> Dict:
        """
        解析用户输入的商品信息
        
        示例输入："上架一个ins风手机壳，适用于iPhone15，售价39元，库存200"
        """
        info = {
            "raw_input": user_input,
            "product_name": "",
            "style": "",
            "category": "",
            "specs": {},
            "price": None,
            "stock": None,
            "target_users": [],
        }
        
        # 提取风格
        style_patterns = ["ins风", "可爱风", "商务风", "极简风", "复古风", "性价比风", "网红风"]
        for style in style_patterns:
            if style in user_input:
                info["style"] = style
                break
        if not info["style"]:
            info["style"] = "通用"
        
        # 提取商品名
        name_patterns = [
            r"([\u4e00-\u9fa5]+(?:手机壳|壳|保护壳|充电器|耳机|数据线|膜))",
            r"([\u4e00-\u9fa5]+(?:衣|裤|裙|鞋|包|饰品))",
            r"([\u4e00-\u9fa5]+(?:零食|食品|饮料))",
            r"([\u4e00-\u9fa5]+(?:化妆品|护肤品|面膜))",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, user_input)
            if match:
                info["product_name"] = match.group(1)
                break
        
        # 提取适用型号/规格
        spec_patterns = [
            r"适用于?\s*([iI]phone\s*\d+[\s\w]*)",
            r"适用于?\s*([\u4e00-\u9fa5\w\s]+?)(?:，|,|；|;|售价|价格|卖)",
            r"([\d.]+)\s*(寸|英寸|cm|毫升|g|克)",
        ]
        for pattern in spec_patterns:
            match = re.search(pattern, user_input)
            if match:
                info["specs"]["model"] = match.group(1).strip()
                break
        
        # 提取价格
        price_match = re.search(r"(?:售价|价格|卖|定价)[^\d]*(\d+)[^\d]*元", user_input)
        if price_match:
            info["price"] = int(price_match.group(1))
        
        # 提取库存
        stock_match = re.search(r"(?:库存|存货|数量)[^\d]*(\d+)", user_input)
        if stock_match:
            info["stock"] = int(stock_match.group(1))
        
        # 推断品类
        info["category"] = self._infer_category(info["product_name"])
        
        # 推断目标用户
        info["target_users"] = self._infer_target_users(info)
        
        return info
    
    def _infer_category(self, product_name: str) -> str:
        """根据商品名推断品类"""
        category_keywords = {
            "手机壳": "手机配件", "充电器": "手机配件", "耳机": "数码配件",
            "数据线": "手机配件", "手机膜": "手机配件",
            "衣": "服饰内衣", "裙": "服饰内衣", "裤": "服饰内衣",
            "鞋": "服饰内衣", "包": "箱包皮具",
            "零食": "食品饮料", "饮料": "食品饮料",
            "化妆品": "美妆护肤", "面膜": "美妆护肤",
        }
        for keyword, category in category_keywords.items():
            if keyword in product_name:
                return category
        return "日用百货"
    
    def _infer_target_users(self, info: Dict) -> List[str]:
        """推断目标用户群体"""
        users = []
        
        # 根据商品推断
        if "手机壳" in info.get("product_name", ""):
            users.extend(["iPhone用户", "手机配件爱好者"])
        if info.get("style") == "ins风":
            users.extend(["年轻女性", "追求生活品质的人群"])
        if info.get("style") == "商务风":
            users.extend(["职场人士", "商务人群"])
        if info.get("style") == "可爱风":
            users.extend(["学生党", "年轻女性"])
        if info.get("price", 100) < 50:
            users.append("价格敏感型消费者")
        
        return list(set(users)) if users else ["通用人群"]
    
    def generate_content(self, product_info: Dict) -> Dict:
        """
        生成完整的商品内容
        """
        style = product_info.get("style", "通用")
        style_config = self.style_presets.get(style, {"tone": "通用", "keywords": []})
        
        # 生成优化标题
        title = self._generate_title(product_info, style_config)
        
        # 生成卖点
        selling_points = self._generate_selling_points(product_info, style_config)
        
        # 生成详情页文案
        detail_content = self._generate_detail(product_info, style_config, selling_points)
        
        # 生成标签
        tags = self._generate_tags(product_info, style_config)
        
        # 生成主图文案建议
        main_image_text = self._generate_main_image_text(product_info, style_config)
        
        return {
            "success": True,
            "product_info": product_info,
            "optimized_content": {
                "title": title,
                "selling_points": selling_points,
                "detail_content": detail_content,
                "tags": tags,
                "main_image_suggestions": main_image_text,
            },
            "ready_to_publish": True,
        }
    
    def _generate_title(self, info: Dict, style_config: Dict) -> str:
        """生成优化标题"""
        name = info.get("product_name", "")
        style = info.get("style", "")
        specs = info.get("specs", {})
        price = info.get("price", 0)
        
        title_parts = []
        
        # 风格词开头
        if style and style != "通用":
            title_parts.append(f"【{style}】")
        
        # 核心商品名
        model = specs.get("model", "")
        if model:
            title_parts.append(f"{model}专用{name}")
        else:
            title_parts.append(name)
        
        # 卖点关键词
        keywords = style_config.get("keywords", [])
        if keywords:
            title_parts.append("".join(keywords[:2]))
        
        # 价格优势（如果价格低）
        if price and price < 50:
            title_parts.append("超值")
        
        title = " | ".join(title_parts)
        
        # 限制长度（微信小店标题通常限制60字符）
        if len(title) > 60:
            title = title[:57] + "..."
        
        return title
    
    def _generate_selling_points(self, info: Dict, style_config: Dict) -> List[Dict]:
        """生成卖点列表"""
        name = info.get("product_name", "")
        style = info.get("style", "")
        specs = info.get("specs", {})
        
        points = []
        emojis = style_config.get("emoji", ["✨", "💫", "⭐", "🔥", "💯"])
        
        # 根据商品类型生成卖点
        if "手机壳" in name:
            points = [
                {"icon": emojis[0], "title": "精准开孔", "desc": f"专为{specs.get('model', '手机')}定制，完美贴合不挡镜头"},
                {"icon": emojis[1], "title": "防摔保护", "desc": "四角气囊设计，有效缓冲跌落冲击，保护爱机"},
                {"icon": emojis[2], "title": "亲肤手感", "desc": "精选优质材质，细腻触感，不发黄不变形"},
                {"icon": emojis[3], "title": f"{style}设计", "desc": f"{style}美学，简约百搭，彰显个人品味"},
            ]
        elif "充电器" in name:
            points = [
                {"icon": "⚡", "title": "快充不伤机", "desc": "智能芯片调控，快充同时保护电池健康"},
                {"icon": "🔒", "title": "多重安全", "desc": "过压/过流/过热保护，充电更安心"},
                {"icon": "📱", "title": "广泛兼容", "desc": "支持多种协议，苹果安卓都能充"},
            ]
        else:
            # 通用卖点
            points = [
                {"icon": emojis[0], "title": "品质保证", "desc": "严选优质材料，精工细作，经久耐用"},
                {"icon": emojis[1], "title": f"{style}设计", "desc": f"{style}美学设计，时尚百搭"},
                {"icon": emojis[2], "title": "性价比之选", "desc": "超值价格，品质不打折"},
                {"icon": emojis[3], "title": "售后无忧", "desc": "7天无理由退换，购物零风险"},
            ]
        
        return points
    
    def _generate_detail(self, info: Dict, style_config: Dict, selling_points: List) -> str:
        """生成详情页文案"""
        name = info.get("product_name", "")
        style = info.get("style", "")
        price = info.get("price", 0)
        
        # 开场白
        openings = {
            "ins风": f"✨ 这款{name}真的太戳我了！",
            "可爱风": f"🎀 萌化了的{name}来啦！",
            "商务风": f"💼 专业品质{name}，职场必备",
            "极简风": f"🤍 Less is more，纯粹{name}",
            "通用": f"🌟 好物推荐 | {name}",
        }
        
        opening = openings.get(style, openings["通用"])
        
        # 构建详情
        lines = [
            opening,
            "",
            "━━━ 🛍️ 商品详情 ━━━",
            f"📦 商品名称：{name}",
            f"🎨 风格：{style}",
        ]
        
        if info.get("specs", {}).get("model"):
            lines.append(f"📱 适用型号：{info['specs']['model']}")
        
        if price:
            lines.append(f"💰 售价：¥{price}")
        
        lines.extend([
            "",
            "━━━ ✨ 核心卖点 ━━━",
        ])
        
        for point in selling_points:
            lines.append(f"{point['icon']} {point['title']}：{point['desc']}")
        
        lines.extend([
            "",
            "━━━ 💡 使用建议 ━━━",
            "• 收到商品后请先检查包装是否完好",
            "• 如有任何问题请联系客服",
            "• 支持7天无理由退换",
            "",
            "━━━ 📦 物流说明 ━━━",
            "• 48小时内发货",
            "• 全国包邮（偏远地区除外）",
            "• 支持指定快递请联系客服",
            "",
            f"💕 喜欢就下单吧！限时优惠价¥{price}" if price else "💕 喜欢就下单吧！",
        ])
        
        return "\n".join(lines)
    
    def _generate_tags(self, info: Dict, style_config: Dict) -> List[str]:
        """生成商品标签"""
        tags = []
        name = info.get("product_name", "")
        style = info.get("style", "")
        category = info.get("category", "")
        
        # 风格标签
        if style and style != "通用":
            tags.append(style)
        
        # 品类标签
        if category:
            tags.append(category)
        
        # 商品特性标签
        if "手机壳" in name:
            tags.extend(["手机配件", "保护壳", "防摔"])
        if info.get("price", 100) < 50:
            tags.append("平价好物")
        if info.get("price", 100) > 200:
            tags.append("品质之选")
        
        # 风格关键词标签
        keywords = style_config.get("keywords", [])
        tags.extend([k for k in keywords if k not in tags])
        
        # 目标用户标签
        tags.extend(info.get("target_users", [])[:2])
        
        # 去重并限制数量
        unique_tags = list(set(tags))
        return unique_tags[:8]  # 最多8个标签
    
    def _generate_main_image_text(self, info: Dict, style_config: Dict) -> List[Dict]:
        """生成主图文案建议"""
        style = info.get("style", "")
        name = info.get("product_name", "")
        price = info.get("price", 0)
        
        suggestions = []
        
        # 第一张主图（首图）
        suggestions.append({
            "image_number": 1,
            "type": "首图（必传）",
            "scene": "白底图或场景图",
            "text_overlay": f"{style}" if style else "",
            "tips": "清晰展示商品全貌，背景简洁",
        })
        
        # 第二张（细节图）
        suggestions.append({
            "image_number": 2,
            "type": "细节图",
            "scene": "材质/做工特写",
            "text_overlay": "精工细作 | 品质可见",
            "tips": "突出质感细节",
        })
        
        # 第三张（场景图）
        if "手机壳" in name:
            suggestions.append({
                "image_number": 3,
                "type": "场景图",
                "scene": "手机佩戴效果",
                "text_overlay": "完美贴合 | 孔位精准",
                "tips": "展示实际使用效果",
            })
        else:
            suggestions.append({
                "image_number": 3,
                "type": "场景图",
                "scene": "使用场景",
                "text_overlay": "日常搭配",
                "tips": "展示实际使用场景",
            })
        
        # 第四张（卖点图）
        suggestions.append({
            "image_number": 4,
            "type": "卖点图",
            "scene": "功能展示",
            "text_overlay": "核心卖点文字",
            "tips": "图文结合突出卖点",
        })
        
        # 第五张（促销图）
        if price and price < 50:
            suggestions.append({
                "image_number": 5,
                "type": "促销图",
                "scene": "价格展示",
                "text_overlay": f"¥{price} 超值价",
                "tips": "突出价格优势",
            })
        
        return suggestions
    
    def process(self, user_input: str) -> Dict:
        """
        主处理流程
        """
        # 1. 解析用户输入
        product_info = self.parse_input(user_input)
        
        # 2. 生成商品内容
        result = self.generate_content(product_info)
        
        return result


# 测试
if __name__ == "__main__":
    agent = ProductAgent()
    
    test_inputs = [
        "上架一个ins风手机壳，适用于iPhone15，售价39元，库存200",
        "可爱风蓝牙耳机，卖99元",
        "商务男士双肩包，298元",
    ]
    
    for inp in test_inputs:
        print(f"\n{'='*60}")
        print(f"输入：{inp}")
        print('='*60)
        
        result = agent.process(inp)
        content = result["optimized_content"]
        
        print(f"\n✅ 优化标题：{content['title']}")
        print(f"\n✅ 卖点列表：")
        for point in content['selling_points']:
            print(f"  {point['icon']} {point['title']}：{point['desc']}")
        print(f"\n✅ 商品标签：{', '.join(content['tags'])}")
        print(f"\n✅ 主图建议：")
        for img in content['main_image_suggestions']:
            print(f"  图{img['image_number']}({img['type']})：{img['scene']} - \"{img['text_overlay']}\"")
