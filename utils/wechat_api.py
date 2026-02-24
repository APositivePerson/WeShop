"""
微信小店API工具
处理access_token获取、微信登录、店铺管理和商品上架
"""

import time
import requests
from typing import Dict, Optional, List
from config import WECHAT_SHOP_CONFIG
import json
from pathlib import Path

# 数据存储路径
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
SHOPS_FILE = DATA_DIR / "shops.json"
USER_SHOPS_FILE = DATA_DIR / "user_shops.json"


class WechatShopAPI:
    """微信小店API客户端 - 增强版，支持登录和店铺管理"""
    
    def __init__(self):
        self.app_id = WECHAT_SHOP_CONFIG["app_id"]
        self.app_secret = WECHAT_SHOP_CONFIG["app_secret"]
        self.access_token = WECHAT_SHOP_CONFIG.get("access_token", "")
        self.token_expire_time = WECHAT_SHOP_CONFIG.get("token_expire_time", 0)
        self.api_base = WECHAT_SHOP_CONFIG["api_base"]
    
    def get_access_token(self) -> Optional[str]:
        """
        获取微信access_token
        如果token过期或不存在，会重新获取
        """
        current_time = int(time.time())
        
        # 如果token还在有效期内（预留60秒缓冲）
        if self.access_token and current_time < self.token_expire_time - 60:
            return self.access_token
        
        # 重新获取token
        url = f"{self.api_base}/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                expires_in = result.get("expires_in", 7200)
                self.token_expire_time = current_time + expires_in
                
                # 更新配置
                WECHAT_SHOP_CONFIG["access_token"] = self.access_token
                WECHAT_SHOP_CONFIG["token_expire_time"] = self.token_expire_time
                
                print(f"[WechatAPI] AccessToken获取成功，有效期{expires_in}秒")
                return self.access_token
            else:
                print(f"[WechatAPI] 获取Token失败: {result}")
                return None
                
        except Exception as e:
            print(f"[WechatAPI] 请求异常: {e}")
            return None
    
    # ==================== 微信登录相关 ====================
    
    def get_login_qr_code(self) -> Dict:
        """
        获取微信登录二维码
        返回二维码URL和scene_id用于轮询登录状态
        """
        token = self.get_access_token()
        if not token:
            return {"success": False, "error": "无法获取access_token"}
        
        # 生成唯一scene_id
        scene_id = f"login_{int(time.time())}_{hash(str(time.time())) % 10000}"
        
        # 创建二维码ticket
        url = f"{self.api_base}/cgi-bin/qrcode/create"
        params = {"access_token": token}
        data = {
            "expire_seconds": 600,  # 10分钟有效期
            "action_name": "QR_STR_SCENE",
            "action_info": {
                "scene": {"scene_str": scene_id}
            }
        }
        
        try:
            response = requests.post(url, params=params, json=data, timeout=10)
            result = response.json()
            
            if "ticket" in result:
                qr_url = f"https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket={result['ticket']}"
                
                # 保存登录会话
                self._save_login_session(scene_id)
                
                return {
                    "success": True,
                    "scene_id": scene_id,
                    "qr_url": qr_url,
                    "expire_seconds": result.get("expire_seconds", 600)
                }
            else:
                return {
                    "success": False,
                    "error": result.get("errmsg", "获取二维码失败")
                }
        except Exception as e:
            return {"success": False, "error": f"请求失败: {str(e)}"}
    
    def check_login_status(self, scene_id: str) -> Dict:
        """
        检查登录状态
        用户扫码后会通过消息推送告知登录结果
        """
        # 这里简化处理，实际应该通过微信消息推送或轮询获取
        sessions = self._load_login_sessions()
        
        if scene_id not in sessions:
            return {"success": False, "error": "登录会话不存在或已过期"}
        
        session = sessions[scene_id]
        
        # 检查是否过期
        if session.get("expire_time", 0) < time.time():
            return {"success": False, "error": "二维码已过期", "expired": True}
        
        # 检查是否已登录
        if session.get("status") == "logged_in" and session.get("openid"):
            # 获取或创建用户
            user = self._get_or_create_user(session["openid"], session.get("user_info", {}))
            
            return {
                "success": True,
                "logged_in": True,
                "user": user,
                "token": self._generate_user_token(user["id"])
            }
        
        return {
            "success": True,
            "logged_in": False,
            "status": session.get("status", "waiting"),
            "message": "等待扫码..."
        }
    
    def mock_login(self, mock_openid: str = None, nickname: str = "测试用户") -> Dict:
        """
        模拟登录（用于开发测试）
        """
        mock_openid = mock_openid or f"mock_{int(time.time())}"
        
        user_info = {
            "openid": mock_openid,
            "nickname": nickname,
            "avatar": "https://via.placeholder.com/100",
            "mock": True
        }
        
        user = self._get_or_create_user(mock_openid, user_info)
        
        return {
            "success": True,
            "user": user,
            "token": self._generate_user_token(user["id"]),
            "mock": True
        }
    
    # ==================== 店铺管理相关 ====================
    
    def get_user_shops(self, user_id: str) -> List[Dict]:
        """
        获取用户关联的店铺列表
        """
        user_shops = self._load_user_shops()
        shops = self._load_shops()
        
        # 获取用户关联的店铺ID列表
        user_shop_ids = user_shops.get(user_id, [])
        
        result = []
        for shop_id in user_shop_ids:
            if shop_id in shops:
                shop = shops[shop_id].copy()
                shop["permissions"] = self._get_user_shop_permissions(user_id, shop_id)
                result.append(shop)
        
        return result
    
    def get_shop_detail(self, shop_id: str, user_id: str = None) -> Optional[Dict]:
        """
        获取店铺详情
        """
        shops = self._load_shops()
        
        if shop_id not in shops:
            return None
        
        shop = shops[shop_id].copy()
        
        if user_id:
            shop["user_permissions"] = self._get_user_shop_permissions(user_id, shop_id)
        
        return shop
    
    def check_shop_permission(self, user_id: str, shop_id: str, action: str = "view") -> bool:
        """
        检查用户对店铺的操作权限
        
        action: view, edit, publish, delete, admin
        """
        user_shops = self._load_user_shops()
        shops = self._load_shops()
        
        # 检查用户是否关联该店铺
        if shop_id not in user_shops.get(user_id, []):
            return False
        
        # 获取用户在店铺中的角色
        shop_user_data = shops.get(shop_id, {}).get("users", {}).get(user_id, {})
        role = shop_user_data.get("role", "viewer")
        
        # 权限映射
        permission_map = {
            "owner": ["view", "edit", "publish", "delete", "admin"],
            "admin": ["view", "edit", "publish", "delete"],
            "editor": ["view", "edit", "publish"],
            "viewer": ["view"]
        }
        
        allowed = permission_map.get(role, [])
        return action in allowed
    
    def associate_shop(self, user_id: str, shop_data: Dict) -> Dict:
        """
        关联店铺到用户
        """
        shops = self._load_shops()
        user_shops = self._load_user_shops()
        
        shop_id = shop_data.get("shop_id") or f"shop_{int(time.time())}"
        
        # 创建或更新店铺
        shops[shop_id] = {
            "id": shop_id,
            "name": shop_data.get("name", "未命名店铺"),
            "logo": shop_data.get("logo", ""),
            "app_id": shop_data.get("app_id", ""),
            "description": shop_data.get("description", ""),
            "created_at": shops.get(shop_id, {}).get("created_at", time.strftime('%Y-%m-%d %H:%M:%S')),
            "updated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "users": {
                user_id: {
                    "role": "owner",  # 创建者是店主
                    "joined_at": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        }
        
        # 关联到用户
        if user_id not in user_shops:
            user_shops[user_id] = []
        if shop_id not in user_shops[user_id]:
            user_shops[user_id].append(shop_id)
        
        self._save_shops(shops)
        self._save_user_shops(user_shops)
        
        return {
            "success": True,
            "shop": shops[shop_id]
        }
    
    def switch_current_shop(self, user_id: str, shop_id: str) -> Dict:
        """
        切换当前操作的店铺
        """
        # 检查是否有权限
        if not self.check_shop_permission(user_id, shop_id, "view"):
            return {"success": False, "error": "没有权限访问该店铺"}
        
        shop = self.get_shop_detail(shop_id, user_id)
        
        if not shop:
            return {"success": False, "error": "店铺不存在"}
        
        return {
            "success": True,
            "shop": shop
        }
    
    # ==================== 商品相关 ====================
    
    def add_product(self, product_data: Dict, user_id: str = None, shop_id: str = None) -> Dict:
        """
        添加商品到微信小店
        带权限验证
        """
        # 权限检查
        if user_id and shop_id:
            if not self.check_shop_permission(user_id, shop_id, "publish"):
                return {"success": False, "error": "没有上架商品权限", "code": "NO_PERMISSION"}
        
        token = self.get_access_token()
        if not token:
            return {"success": False, "error": "无法获取access_token"}
        
        # 微信小店商品添加接口
        url = f"{self.api_base}/shop/product/add"
        
        # 构建请求参数
        params = {"access_token": token}
        
        # 微信小店商品数据结构
        wx_product = {
            "title": product_data.get("title", "")[:30],
            "path": "pages/index/index",
            "head_img": product_data.get("main_image", []),
            "desc_info": {
                "desc": product_data.get("detail", "")[:500],
                "imgs": product_data.get("images", [])[:9],
            },
            "price": int(product_data.get("price", 0) * 100),
            "stock_num": product_data.get("stock", 0),
        }
        
        if "skus" in product_data:
            wx_product["skus"] = product_data["skus"]
        
        try:
            response = requests.post(
                url,
                params=params,
                json=wx_product,
                timeout=30
            )
            result = response.json()
            
            if result.get("errcode") == 0:
                return {
                    "success": True,
                    "product_id": result.get("data", {}).get("product_id"),
                    "message": "上架成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("errmsg", "未知错误"),
                    "errcode": result.get("errcode")
                }
                
        except Exception as e:
            return {"success": False, "error": f"请求失败: {str(e)}"}
    
    def get_product_list(self, page: int = 1, page_size: int = 10, shop_id: str = None) -> Dict:
        """
        获取商品列表
        可以指定店铺ID获取特定店铺的商品
        """
        token = self.get_access_token()
        if not token:
            return {"success": False, "error": "无法获取access_token"}
        
        url = f"{self.api_base}/shop/product/get_list"
        params = {"access_token": token}
        data = {
            "page": page,
            "page_size": page_size
        }
        
        if shop_id:
            data["shop_id"] = shop_id
        
        try:
            response = requests.post(url, params=params, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                return {"success": True, "products": result.get("data", {}).get("products", [])}
            else:
                return {"success": False, "error": result.get("errmsg")}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== 数据存储相关（私有方法） ====================
    
    def _load_json(self, filepath: Path, default=None):
        """加载JSON文件"""
        default = default or {}
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    
    def _save_json(self, filepath: Path, data):
        """保存JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_login_sessions(self):
        """加载登录会话"""
        filepath = DATA_DIR / "login_sessions.json"
        return self._load_json(filepath, {})
    
    def _save_login_session(self, scene_id: str, status: str = "waiting", user_info: Dict = None):
        """保存登录会话"""
        sessions = self._load_login_sessions()
        sessions[scene_id] = {
            "scene_id": scene_id,
            "status": status,
            "create_time": time.time(),
            "expire_time": time.time() + 600,
            "user_info": user_info or {}
        }
        self._save_json(DATA_DIR / "login_sessions.json", sessions)
    
    def _load_users(self):
        """加载用户数据"""
        return self._load_json(USERS_FILE, {})
    
    def _save_users(self, users):
        """保存用户数据"""
        self._save_json(USERS_FILE, users)
    
    def _load_shops(self):
        """加载店铺数据"""
        return self._load_json(SHOPS_FILE, {})
    
    def _save_shops(self, shops):
        """保存店铺数据"""
        self._save_json(SHOPS_FILE, shops)
    
    def _load_user_shops(self):
        """加载用户-店铺关联数据"""
        return self._load_json(USER_SHOPS_FILE, {})
    
    def _save_user_shops(self, user_shops):
        """保存用户-店铺关联数据"""
        self._save_json(USER_SHOPS_FILE, user_shops)
    
    def _get_or_create_user(self, openid: str, user_info: Dict) -> Dict:
        """获取或创建用户"""
        users = self._load_users()
        
        if openid not in users:
            user_id = f"user_{int(time.time())}_{hash(openid) % 10000}"
            users[openid] = {
                "id": user_id,
                "openid": openid,
                "nickname": user_info.get("nickname", "微信用户"),
                "avatar": user_info.get("avatar", ""),
                "created_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "last_login": time.strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            users[openid]["last_login"] = time.strftime('%Y-%m-%d %H:%M:%S')
            if user_info.get("nickname"):
                users[openid]["nickname"] = user_info["nickname"]
            if user_info.get("avatar"):
                users[openid]["avatar"] = user_info["avatar"]
        
        self._save_users(users)
        return users[openid]
    
    def _generate_user_token(self, user_id: str) -> str:
        """生成用户会话token"""
        import hashlib
        token = hashlib.sha256(f"{user_id}_{time.time()}_{self.app_secret}".encode()).hexdigest()[:32]
        
        # 保存token映射
        tokens = self._load_json(DATA_DIR / "tokens.json", {})
        tokens[token] = {
            "user_id": user_id,
            "create_time": time.time(),
            "expire_time": time.time() + 7 * 24 * 3600  # 7天有效期
        }
        self._save_json(DATA_DIR / "tokens.json", tokens)
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """验证token并返回用户信息"""
        tokens = self._load_json(DATA_DIR / "tokens.json", {})
        
        if token not in tokens:
            return None
        
        token_data = tokens[token]
        
        # 检查是否过期
        if token_data.get("expire_time", 0) < time.time():
            return None
        
        # 获取用户信息
        users = self._load_users()
        for user in users.values():
            if user["id"] == token_data["user_id"]:
                return user
        
        return None
    
    def _get_user_shop_permissions(self, user_id: str, shop_id: str) -> List[str]:
        """获取用户在店铺中的权限列表"""
        shops = self._load_shops()
        
        if shop_id not in shops:
            return []
        
        shop_user_data = shops[shop_id].get("users", {}).get(user_id, {})
        role = shop_user_data.get("role", "viewer")
        
        permission_map = {
            "owner": ["view", "edit", "publish", "delete", "admin"],
            "admin": ["view", "edit", "publish", "delete"],
            "editor": ["view", "edit", "publish"],
            "viewer": ["view"]
        }
        
        return permission_map.get(role, ["view"])


# 全局API实例
wechat_api = WechatShopAPI()
