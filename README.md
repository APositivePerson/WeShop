# 微信小店AI上架助手

面向微信小店商家的 AI Agent 平台，一句话描述商品，AI自动生成优化标题、卖点、详情页，一键上架。

![演示](https://img.shields.io/badge/微信小店-AI助手-07C160)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB)

## ✨ 功能特性

- 🤖 **AI文案生成** - 输入商品描述，自动生成完整商品信息
- 🏷️ **智能标题优化** - 生成吸引眼球的商品标题
- ✨ **卖点提炼** - 自动提取并包装商品卖点
- 📝 **详情页文案** - 一键生成详情页完整文案
- 🏷️ **商品标签** - 智能推荐商品标签
- 📸 **主图文案** - 提供主图拍摄和文案建议
- 🚀 **一键上架** - 对接微信小店API快速上架

## 🚀 快速开始

### 1. 克隆项目

```bash
cd wechat-shop-ai
```

### 2. 安装依赖

```bash
pip install fastapi uvicorn pydantic
```

### 3. 启动服务

```bash
./start.sh
# 或
python backend/main.py
```

### 4. 访问

- 前端页面: http://localhost:8080
- API文档: http://localhost:8080/docs

## 📖 使用示例

### 商家输入
```
上架一个ins风手机壳，适用于iPhone15，售价39元，库存200
```

### 系统输出

| 项目 | 内容 |
|------|------|
| **✅ 优化标题** | 【ins风】iPhone15专用手机壳 \| 简约质感 \| 超值 |
| **✅ 卖点列表** | 🎯 精准开孔、💪 防摔保护、🤲 亲肤手感、✨ ins风设计 |
| **✅ 详情页** | 完整文案（含使用建议、物流说明） |
| **✅ 商品标签** | ins风、手机配件、平价好物、年轻女性 |
| **✅ 主图文案** | 5张主图的拍摄建议和文案 |

然后点击 **【一键上架】** 即可发布到微信小店！

## 📁 项目结构

```
wechat-shop-ai/
├── backend/
│   └── main.py           # FastAPI后端服务
├── agents/
│   └── product_agent.py  # AI商品生成Agent
├── frontend/
│   ├── index.html        # 前端页面
│   ├── style.css         # 样式
│   └── app.js            # 前端逻辑
├── config.py             # 配置文件
├── start.sh              # 启动脚本
└── README.md
```

## 🔧 API接口

### 生成商品内容
```bash
POST /api/generate
Content-Type: application/json

{
    "description": "ins风手机壳，iPhone15，39元"
}
```

### 一键上架
```bash
POST /api/publish
Content-Type: application/json

{
    "product_info": {...},
    "content": {...}
}
```

## 🎨 支持的风格

| 风格 | 特点 |
|------|------|
| ins风 | 清新文艺、简约时尚 |
| 可爱风 | 萌系甜美、少女心 |
| 商务风 | 专业品质、职场必备 |
| 极简风 | Less is more |
| 复古风 | 怀旧经典 |
| 性价比风 | 超值特惠 |

## ⚙️ 配置说明

编辑 `config.py` 配置：

```python
# 微信小店API（需申请）
WECHAT_SHOP_CONFIG = {
    "app_id": "your_app_id",
    "app_secret": "your_app_secret",
}
```

## 📝 接入微信小店API

当前版本为演示模式，如需真实上架，需：

1. 申请微信小店接入权限
2. 在 `config.py` 中配置 `app_id` 和 `app_secret`
3. 在 `backend/main.py` 中实现 `publish_product` 函数调用微信API

微信小店商品添加API：
```
POST https://api.weixin.qq.com/shop/product/add
```

## 🛣️ 后续规划

- [ ] 接入LLM API（GPT/Claude）增强文案质量
- [ ] 图片AI生成/优化
- [ ] 价格智能建议
- [ ] 竞品分析
- [ ] 库存预警
- [ ] 数据分析看板

---

有问题或建议？欢迎提Issue！
