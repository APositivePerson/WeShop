"""
FastAPI 后端服务 - 增强版
提供商品生成、上架API、微信登录、店铺管理和权限验证
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import json
from pathlib import Path

from agents.product_agent import ProductAgent
from utils.wechat_api import wechat_api
from config import API_CONFIG, WECHAT_SHOP_CONFIG
import time

# 基础路径定义
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="微信小店AI上架助手",
    description="AI驱动的商品文案生成与上架平台 - 支持微信登录和店铺管理",
    version="2.0.0"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化Agent
product_agent = ProductAgent()

# 商品存储（简单JSON文件存储）
PRODUCTS_FILE = DATA_DIR / "products.json"
USER_PRODUCTS_FILE = DATA_DIR / "user_products.json"


def load_products():
    """加载已上架商品列表"""
    if PRODUCTS_FILE.exists():
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_product(product_data):
    """保存商品到列表"""
    products = load_products()
    product_data['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    products.insert(0, product_data)
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    return product_data


# ============ 认证依赖 ============

async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    获取当前登录用户
    从请求头中提取token并验证
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录，请先登录")
    
    # 支持 "Bearer token" 或纯 token 格式
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    user = wechat_api.verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    
    return user


# ============ 数据模型 ============

class ProductInput(BaseModel):
    """商品输入"""
    description: str


class ProductContent(BaseModel):
    """生成的商品内容"""
    title: str
    selling_points: List[Dict]
    detail_content: str
    tags: List[str]
    main_image_suggestions: List[Dict]


class GenerateResponse(BaseModel):
    """生成响应"""
    success: bool
    product_info: Dict
    optimized_content: ProductContent
    ready_to_publish: bool


class PublishRequest(BaseModel):
    """上架请求"""
    product_info: Dict
    content: Dict
    images: Optional[List[str]] = None
    shop_id: Optional[str] = None  # 指定上架到哪个店铺


class PublishResponse(BaseModel):
    """上架响应"""
    success: bool
    message: str
    product_id: Optional[str] = None
    shop_url: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""
    scene_id: Optional[str] = None
    mock: bool = False  # 模拟登录，用于测试


class AssociateShopRequest(BaseModel):
    """关联店铺请求"""
    shop_name: str
    app_id: Optional[str] = None
    description: Optional[str] = None


class SwitchShopRequest(BaseModel):
    """切换店铺请求"""
    shop_id: str


# ============ API接口 - 认证相关 ============

@app.get("/")
def read_root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/login")
def login_page():
    """登录页面"""
    return FileResponse(FRONTEND_DIR / "login.html")


@app.get("/settings")
def settings_page():
    """设置页面"""
    return FileResponse(FRONTEND_DIR / "settings.html")


@app.post("/api/auth/qr-code")
def get_login_qr_code():
    """
    获取微信登录二维码
    
    返回二维码URL和scene_id，前端需要轮询检查登录状态
    """
    result = wechat_api.get_login_qr_code()
    return result


@app.post("/api/auth/check")
def check_login_status(data: LoginRequest):
    """
    检查登录状态
    
    前端轮询此接口检查用户是否已扫码登录
    """
    if data.mock:
        # 模拟登录模式（开发测试用）
        result = wechat_api.mock_login()
        return result
    
    if not data.scene_id:
        raise HTTPException(status_code=400, detail="缺少scene_id参数")
    
    result = wechat_api.check_login_status(data.scene_id)
    return result


@app.post("/api/auth/logout")
def logout(user: Dict = Depends(get_current_user)):
    """
    用户登出
    """
    # 可以在这里使token失效
    return {"success": True, "message": "已退出登录"}


@app.get("/api/auth/me")
def get_current_user_info(user: Dict = Depends(get_current_user)):
    """
    获取当前登录用户信息
    """
    return {
        "success": True,
        "user": user
    }


# ============ API接口 - 店铺管理 ============

@app.get("/api/shops")
def get_user_shops(user: Dict = Depends(get_current_user)):
    """
    获取当前用户关联的所有店铺
    """
    shops = wechat_api.get_user_shops(user["id"])
    return {
        "success": True,
        "shops": shops,
        "count": len(shops)
    }


@app.post("/api/shops/associate")
def associate_shop(data: AssociateShopRequest, user: Dict = Depends(get_current_user)):
    """
    关联微信小店到当前用户
    
    用户可以选择关联已有的微信小店，创建关联关系
    """
    shop_data = {
        "name": data.shop_name,
        "app_id": data.app_id or WECHAT_SHOP_CONFIG["app_id"],
        "description": data.description or ""
    }
    
    result = wechat_api.associate_shop(user["id"], shop_data)
    return result


@app.post("/api/shops/switch")
def switch_current_shop(data: SwitchShopRequest, user: Dict = Depends(get_current_user)):
    """
    切换当前操作的店铺
    
    用户可以选择切换到不同的店铺进行操作
    """
    result = wechat_api.switch_current_shop(user["id"], data.shop_id)
    return result


@app.get("/api/shops/{shop_id}")
def get_shop_detail(shop_id: str, user: Dict = Depends(get_current_user)):
    """
    获取店铺详情，包括当前用户在该店铺的权限
    """
    shop = wechat_api.get_shop_detail(shop_id, user["id"])
    
    if not shop:
        raise HTTPException(status_code=404, detail="店铺不存在")
    
    # 检查是否有权限查看
    if not wechat_api.check_shop_permission(user["id"], shop_id, "view"):
        raise HTTPException(status_code=403, detail="没有权限查看该店铺")
    
    return {
        "success": True,
        "shop": shop
    }


@app.get("/api/shops/{shop_id}/permissions")
def get_shop_permissions(shop_id: str, user: Dict = Depends(get_current_user)):
    """
    获取当前用户在指定店铺的权限列表
    """
    if not wechat_api.check_shop_permission(user["id"], shop_id, "view"):
        raise HTTPException(status_code=403, detail="没有权限查看该店铺")
    
    permissions = wechat_api._get_user_shop_permissions(user["id"], shop_id)
    
    return {
        "success": True,
        "shop_id": shop_id,
        "permissions": permissions,
        "can_publish": "publish" in permissions,
        "can_edit": "edit" in permissions,
        "can_delete": "delete" in permissions,
        "is_admin": "admin" in permissions
    }


# ============ API接口 - 商品生成与上架 ============

@app.post("/api/generate", response_model=GenerateResponse)
def generate_product(data: ProductInput, user: Dict = Depends(get_current_user)):
    """
    生成商品内容
    
    需要登录后才能使用
    """
    try:
        if not data.description or len(data.description.strip()) < 5:
            raise HTTPException(status_code=400, detail="描述太短，请提供更多商品信息")
        
        result = product_agent.process(data.description)
        
        # 添加用户信息
        result["user_id"] = user["id"]
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@app.post("/api/preview")
def preview_product(data: ProductInput, user: Dict = Depends(get_current_user)):
    """
    预览生成的商品内容（不保存）
    """
    return generate_product(data, user)


@app.post("/api/publish", response_model=PublishResponse)
def publish_product(data: PublishRequest, user: Dict = Depends(get_current_user)):
    """
    一键上架商品到微信小店
    
    权限验证：
    - 如果没有指定shop_id，使用用户默认店铺（第一个关联店铺）
    - 检查用户是否有该店铺的publish权限
    """
    try:
        shop_id = data.shop_id
        
        # 如果没有指定店铺，获取用户的第一个店铺
        if not shop_id:
            user_shops = wechat_api.get_user_shops(user["id"])
            if not user_shops:
                return PublishResponse(
                    success=False,
                    message="您还没有关联任何店铺，请先关联店铺",
                    product_id=None
                )
            shop_id = user_shops[0]["id"]
        
        # 检查权限
        if not wechat_api.check_shop_permission(user["id"], shop_id, "publish"):
            return PublishResponse(
                success=False,
                message="没有上架商品权限，请联系店铺管理员",
                product_id=None
            )
        
        # 构建商品数据
        product_info = data.product_info
        content = data.content
        
        wx_product_data = {
            "title": content.get("title", ""),
            "price": product_info.get("price", 0),
            "stock": product_info.get("stock", 0),
            "detail": content.get("detail_content", ""),
            "main_image": data.images or [],
            "tags": content.get("tags", []),
            "selling_points": [sp.get("content", "") for sp in content.get("selling_points", [])]
        }
        
        # 调用微信小店API上架（带用户ID和店铺ID进行权限验证）
        result = wechat_api.add_product(wx_product_data, user_id=user["id"], shop_id=shop_id)
        
        if result.get("success"):
            # 保存到本地商品库
            saved_product = {
                "product_id": result.get("product_id"),
                "title": content.get("title"),
                "price": product_info.get("price"),
                "stock": product_info.get("stock"),
                "status": "已上架",
                "content": content,
                "user_id": user["id"],
                "shop_id": shop_id,
                "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            save_product(saved_product)
            
            return PublishResponse(
                success=True,
                message="商品已成功上架到微信小店！",
                product_id=result.get("product_id"),
                shop_url=f"https://shop.weixin.qq.com/"
            )
        else:
            # API调用失败，返回错误信息
            error_msg = result.get("error", "未知错误")
            errcode = result.get("errcode", "")
            
            # 处理权限错误
            if result.get("code") == "NO_PERMISSION":
                return PublishResponse(
                    success=False,
                    message=f"权限不足: {error_msg}",
                    product_id=None
                )
            
            return PublishResponse(
                success=False,
                message=f"上架失败: {error_msg} (错误码: {errcode})",
                product_id=None,
                shop_url=None
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上架失败: {str(e)}")


@app.post("/api/regenerate")
def regenerate_content(data: ProductInput, user: Dict = Depends(get_current_user)):
    """
    重新生成内容（可以添加随机性）
    """
    return generate_product(data, user)


@app.get("/api/templates")
def get_templates():
    """
    获取商品描述模板（无需登录）
    """
    templates = [
        {
            "category": "手机配件",
            "examples": [
                "上架一个ins风手机壳，适用于iPhone15，售价39元，库存200",
                "可爱卡通AirPods保护套，55元",
                "20W快充充电器，支持苹果PD协议，79元"
            ]
        },
        {
            "category": "服饰内衣",
            "examples": [
                "极简风纯棉T恤，白色M码，69元",
                "复古格纹衬衫，男女同款，128元",
                "ins风针织开衫，秋冬款，159元"
            ]
        },
        {
            "category": "美妆护肤",
            "examples": [
                "补水保湿面膜10片装，39.9元",
                "ins风化妆刷套装，7支装，49元",
                "天然植物护手霜3支，29.9元"
            ]
        },
        {
            "category": "食品饮料",
            "examples": [
                "网红手工牛轧糖，500g，35元",
                "进口咖啡豆，中度烘焙，250g，68元",
                "ins风花果茶礼盒，送礼佳品，88元"
            ]
        }
    ]
    return {"success": True, "templates": templates}


@app.get("/api/styles")
def get_styles():
    """
    获取支持的风格列表（无需登录）
    """
    styles = [
        {"id": "ins风", "name": "ins风", "desc": "清新文艺，简约时尚"},
        {"id": "可爱风", "name": "可爱风", "desc": "萌系甜美，少女心"},
        {"id": "商务风", "name": "商务风", "desc": "专业品质，职场必备"},
        {"id": "极简风", "name": "极简风", "desc": "Less is more"},
        {"id": "复古风", "name": "复古风", "desc": "怀旧经典"},
        {"id": "性价比风", "name": "性价比风", "desc": "超值特惠"},
    ]
    return {"success": True, "styles": styles}


# ============ API接口 - 商品管理 ============

@app.get("/api/products")
def get_products(
    source: str = "local",
    shop_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    user: Dict = Depends(get_current_user)
):
    """
    获取商品列表
    
    - source=local: 获取本地已上架商品（按用户过滤）
    - source=wechat: 从微信小店API获取商品（需要shop_id和权限）
    """
    if source == "wechat":
        # 需要指定店铺
        if not shop_id:
            user_shops = wechat_api.get_user_shops(user["id"])
            if user_shops:
                shop_id = user_shops[0]["id"]
            else:
                return {"success": False, "error": "没有关联的店铺", "products": []}
        
        # 检查权限
        if not wechat_api.check_shop_permission(user["id"], shop_id, "view"):
            return {"success": False, "error": "没有权限查看该店铺的商品", "products": []}
        
        # 从微信小店API获取
        result = wechat_api.get_product_list(page, page_size, shop_id)
        if result.get("success"):
            return {
                "success": True,
                "source": "wechat",
                "shop_id": shop_id,
                "products": result.get("products", [])
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "获取失败"),
                "products": []
            }
    else:
        # 获取本地商品（只显示当前用户的）
        products = load_products()
        user_products = [p for p in products if p.get("user_id") == user["id"]]
        
        # 按店铺过滤
        if shop_id:
            user_products = [p for p in user_products if p.get("shop_id") == shop_id]
        
        return {
            "success": True,
            "source": "local",
            "count": len(user_products),
            "products": user_products
        }


@app.post("/api/products/sync")
def sync_products_from_wechat(
    shop_id: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    """
    从微信小店同步商品到本地
    
    需要指定店铺并有查看权限
    """
    # 获取默认店铺
    if not shop_id:
        user_shops = wechat_api.get_user_shops(user["id"])
        if user_shops:
            shop_id = user_shops[0]["id"]
        else:
            return {"success": False, "error": "没有关联的店铺"}
    
    # 检查权限
    if not wechat_api.check_shop_permission(user["id"], shop_id, "view"):
        return {"success": False, "error": "没有权限同步该店铺的商品"}
    
    result = wechat_api.get_product_list(page=1, page_size=100, shop_id=shop_id)
    
    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error", "同步失败")
        }
    
    wechat_products = result.get("products", [])
    
    # 保存到本地
    for p in wechat_products:
        p['synced_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        p['status'] = '已同步'
        p['user_id'] = user["id"]
        p['shop_id'] = shop_id
    
    # 合并到现有商品列表
    all_products = load_products()
    
    # 删除旧的同步记录
    all_products = [p for p in all_products if not (p.get("shop_id") == shop_id and p.get("status") == "已同步")]
    
    # 添加新的同步记录
    all_products.extend(wechat_products)
    
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    
    return {
        "success": True,
        "message": f"成功同步 {len(wechat_products)} 个商品",
        "count": len(wechat_products),
        "shop_id": shop_id
    }


@app.delete("/api/products/{product_id}")
def delete_product(product_id: str, user: Dict = Depends(get_current_user)):
    """
    删除已上架商品（本地记录）
    
    需要是商品所有者或有删除权限
    """
    products = load_products()
    
    # 查找商品
    product = None
    for p in products:
        if p.get("product_id") == product_id:
            product = p
            break
    
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 检查权限（所有者或有删除权限）
    if product.get("user_id") != user["id"]:
        shop_id = product.get("shop_id")
        if shop_id and not wechat_api.check_shop_permission(user["id"], shop_id, "delete"):
            raise HTTPException(status_code=403, detail="没有权限删除该商品")
    
    # 删除商品
    products = [p for p in products if p.get("product_id") != product_id]
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    return {"success": True, "message": "商品已删除"}


# ============ API接口 - 配置相关 ============

@app.get("/api/config/current")
def get_current_config(user: Dict = Depends(get_current_user)):
    """
    获取当前配置（不包含敏感信息）
    """
    token = wechat_api.get_access_token()
    shop_info = None
    
    # 获取用户店铺
    user_shops = wechat_api.get_user_shops(user["id"])
    
    if token and user_shops:
        # 尝试获取第一个店铺的商品数量
        product_result = wechat_api.get_product_list(1, 1, user_shops[0]["id"] if user_shops else None)
        if product_result.get("success"):
            shop_info = {
                "shop_name": user_shops[0]["name"] if user_shops else "微信小店",
                "product_count": len(product_result.get("products", [])),
                "status": "正常",
                "shops_count": len(user_shops)
            }
    
    return {
        "connected": token is not None,
        "config": {
            "app_id": WECHAT_SHOP_CONFIG.get("app_id", "")[:8] + "..."
        },
        "shop_info": shop_info,
        "user": {
            "id": user["id"],
            "nickname": user.get("nickname", "")
        }
    }


@app.post("/api/config/test")
def test_wechat_config_api(data: Dict = None):
    """
    测试微信小店API配置是否正确（使用传入的参数）
    """
    if data and data.get("app_id") and data.get("app_secret"):
        import requests
        
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": data["app_id"],
            "secret": data["app_secret"]
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if "access_token" in result:
                return {
                    "success": True,
                    "message": f"API配置正确，Token获取成功",
                    "app_id": data["app_id"][:8] + "..."
                }
            else:
                return {
                    "success": False,
                    "message": f"配置错误: {result.get('errmsg', '未知错误')}"
                }
        except Exception as e:
            return {"success": False, "message": f"请求失败: {str(e)}"}
    
    # 使用当前配置测试
    token = wechat_api.get_access_token()
    if token:
        return {
            "success": True,
            "message": "API配置正确，Token获取成功",
            "app_id": WECHAT_SHOP_CONFIG["app_id"][:8] + "...",
            "token_preview": token[:10] + "..."
        }
    else:
        return {
            "success": False,
            "message": "API配置错误，无法获取Token，请检查app_id和app_secret",
            "app_id": WECHAT_SHOP_CONFIG["app_id"]
        }


@app.post("/api/config/save")
def save_config(data: Dict, user: Dict = Depends(get_current_user)):
    """
    保存微信小店配置
    """
    if data.get("app_id"):
        WECHAT_SHOP_CONFIG["app_id"] = data["app_id"]
    if data.get("app_secret"):
        WECHAT_SHOP_CONFIG["app_secret"] = data["app_secret"]
    
    # 清除旧token，强制重新获取
    WECHAT_SHOP_CONFIG["access_token"] = ""
    WECHAT_SHOP_CONFIG["token_expire_time"] = 0
    wechat_api.access_token = ""
    wechat_api.token_expire_time = 0
    
    # 测试新配置
    token = wechat_api.get_access_token()
    
    if token:
        return {
            "success": True,
            "message": "配置保存成功，API连接正常"
        }
    else:
        return {
            "success": False,
            "message": "配置已保存，但API连接失败，请检查AppID和AppSecret"
        }


@app.get("/health")
def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "微信小店AI上架助手",
        "version": "2.0.0",
        "features": ["微信登录", "店铺管理", "权限验证", "AI商品生成"]
    }


# 挂载静态文件
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


if __name__ == "__main__":
    print("🚀 启动微信小店AI上架助手 v2.0...")
    print(f"📍 API文档: http://{API_CONFIG['host']}:{API_CONFIG['port']}/docs")
    print(f"🌐 前端页面: http://{API_CONFIG['host']}:{API_CONFIG['port']}/")
    print("✨ 新功能: 微信登录、店铺管理、权限验证")
    
    uvicorn.run(
        "main:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=API_CONFIG["debug"]
    )
