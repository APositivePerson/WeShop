# AI商品上架助手 - 配置
import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent.parent

# OpenAI/大模型配置
LLM_CONFIG = {
    "model": "kimi-k2.5",  # 或其他可用模型
    "temperature": 0.7,
    "max_tokens": 2000,
}

# 微信小店API配置
WECHAT_SHOP_CONFIG = {
    "app_id": "wx3222966cf5f1d1ac",
    "app_secret": "9b35f2083bbb969684cdd1e8ecc753cf",
    "access_token": "",  # 自动获取
    "token_expire_time": 0,  # token过期时间
    "api_base": "https://api.weixin.qq.com",
}

# 商品类别映射
CATEGORY_MAP = {
    "手机壳": {"id": 1001, "name": "手机配件", "sub": "保护壳/套"},
    "充电器": {"id": 1002, "name": "手机配件", "sub": "充电器"},
    "耳机": {"id": 1003, "name": "数码配件", "sub": "耳机/耳麦"},
    "衣服": {"id": 2001, "name": "服饰内衣", "sub": "女装"},
    "鞋子": {"id": 2002, "name": "服饰内衣", "sub": "男鞋"},
    "包包": {"id": 2003, "name": "箱包皮具", "sub": "女包"},
    "化妆品": {"id": 3001, "name": "美妆护肤", "sub": "面部护肤"},
    "零食": {"id": 4001, "name": "食品饮料", "sub": "休闲零食"},
    "家居": {"id": 5001, "name": "家居日用", "sub": "家居饰品"},
}

# 文案风格模板
STYLE_TEMPLATES = {
    "ins风": {
        "tone": "清新、文艺、简约",
        "keywords": ["简约", "质感", " lifestyle", " aesthetic", "治愈系"],
        "emoji": ["✨", "🤍", "📱", "💫", "🌿"],
    },
    "可爱风": {
        "tone": "活泼、萌系、甜美",
        "keywords": ["萌", "甜", "可爱", "少女心", "治愈"],
        "emoji": ["🎀", "💕", "🌸", "✨", "🐰"],
    },
    "商务风": {
        "tone": "专业、品质、高端",
        "keywords": ["品质", "专业", "商务", "高端", "精选"],
        "emoji": ["💼", "✓", "⭐", "🔒", "📦"],
    },
    "性价比风": {
        "tone": "实惠、划算、超值",
        "keywords": ["超值", "特惠", "爆款", "必入", "性价比"],
        "emoji": ["🔥", "💰", "⚡", "🎉", "💯"],
    },
}

# API配置
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": True,
}
