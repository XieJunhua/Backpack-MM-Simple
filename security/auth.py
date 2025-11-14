"""
Web认证模块
提供基于Token的身份验证机制
"""
import os
import secrets
import hashlib
import time
from typing import Optional, Dict
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from logger import setup_logger

logger = setup_logger("security.auth")


class TokenAuth:
    """Token认证管理器"""

    def __init__(self, token_expiry_hours: int = 24):
        """
        初始化认证管理器

        Args:
            token_expiry_hours: Token过期时间(小时)
        """
        self.token_expiry_hours = token_expiry_hours
        self.active_tokens: Dict[str, Dict] = {}  # {token: {username, expires_at, created_at}}
        self.users: Dict[str, str] = {}  # {username: hashed_password}

        # 从环境变量加载管理员账户
        self._load_admin_user()

    def _load_admin_user(self):
        """从环境变量加载管理员账户"""
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD')

        if not admin_password:
            # 生成随机密码
            admin_password = secrets.token_urlsafe(16)
            logger.warning(f"未设置ADMIN_PASSWORD,生成随机密码: {admin_password}")
            logger.warning("请保存此密码并设置到环境变量ADMIN_PASSWORD中")

        # 存储哈希密码
        self.users[admin_username] = self._hash_password(admin_password)
        logger.info(f"管理员账户已加载: {admin_username}")

    def _hash_password(self, password: str) -> str:
        """
        哈希密码

        Args:
            password: 明文密码

        Returns:
            哈希后的密码
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, username: str, password: str) -> bool:
        """
        验证密码

        Args:
            username: 用户名
            password: 密码

        Returns:
            是否验证通过
        """
        if username not in self.users:
            return False

        hashed = self._hash_password(password)
        return secrets.compare_digest(hashed, self.users[username])

    def generate_token(self, username: str) -> Optional[str]:
        """
        生成访问Token

        Args:
            username: 用户名

        Returns:
            Token字符串或None
        """
        if username not in self.users:
            logger.warning(f"用户不存在: {username}")
            return None

        # 生成安全的随机Token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=self.token_expiry_hours)

        self.active_tokens[token] = {
            'username': username,
            'expires_at': expires_at,
            'created_at': datetime.now(),
            'last_used': datetime.now()
        }

        logger.info(f"为用户 {username} 生成新Token,过期时间: {expires_at}")
        return token

    def verify_token(self, token: str) -> bool:
        """
        验证Token有效性

        Args:
            token: Token字符串

        Returns:
            是否有效
        """
        if token not in self.active_tokens:
            return False

        token_info = self.active_tokens[token]
        if datetime.now() > token_info['expires_at']:
            # Token已过期,删除
            del self.active_tokens[token]
            logger.info(f"Token已过期并被删除: {token[:10]}...")
            return False

        # 更新最后使用时间
        token_info['last_used'] = datetime.now()
        return True

    def revoke_token(self, token: str) -> bool:
        """
        撤销Token

        Args:
            token: Token字符串

        Returns:
            是否成功撤销
        """
        if token in self.active_tokens:
            username = self.active_tokens[token]['username']
            del self.active_tokens[token]
            logger.info(f"Token已撤销: {username}")
            return True
        return False

    def cleanup_expired_tokens(self):
        """清理过期的Token"""
        now = datetime.now()
        expired = [
            token for token, info in self.active_tokens.items()
            if now > info['expires_at']
        ]

        for token in expired:
            del self.active_tokens[token]

        if expired:
            logger.info(f"清理了 {len(expired)} 个过期Token")

    def add_user(self, username: str, password: str) -> bool:
        """
        添加新用户

        Args:
            username: 用户名
            password: 密码

        Returns:
            是否成功添加
        """
        if username in self.users:
            logger.warning(f"用户已存在: {username}")
            return False

        self.users[username] = self._hash_password(password)
        logger.info(f"新用户已添加: {username}")
        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        修改密码

        Args:
            username: 用户名
            old_password: 旧密码
            new_password: 新密码

        Returns:
            是否成功修改
        """
        if not self.verify_password(username, old_password):
            logger.warning(f"修改密码失败: 旧密码错误 - {username}")
            return False

        self.users[username] = self._hash_password(new_password)
        logger.info(f"密码已修改: {username}")
        return True


# 全局认证实例
_auth_instance: Optional[TokenAuth] = None


def get_auth_instance() -> TokenAuth:
    """获取全局认证实例"""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = TokenAuth()
    return _auth_instance


def require_auth(f):
    """
    Flask路由装饰器,要求请求必须携带有效Token

    使用方法:
        @app.route('/api/protected')
        @require_auth
        def protected_route():
            return jsonify({'message': 'Success'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = get_auth_instance()

        # 从请求头获取Token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': '未提供认证Token'}), 401

        # 解析Bearer Token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                return jsonify({'error': '无效的认证方案,请使用Bearer'}), 401
        except ValueError:
            return jsonify({'error': '无效的Authorization头格式'}), 401

        # 验证Token
        if not auth.verify_token(token):
            return jsonify({'error': 'Token无效或已过期'}), 401

        # Token有效,执行原函数
        return f(*args, **kwargs)

    return decorated_function


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    速率限制装饰器

    Args:
        max_requests: 时间窗口内最大请求数
        window_seconds: 时间窗口大小(秒)
    """
    request_history: Dict[str, list] = {}

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取客户端标识(IP或Token)
            client_id = request.remote_addr
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    _, token = auth_header.split()
                    client_id = token[:16]  # 使用Token前16位作为标识
                except:
                    pass

            now = time.time()

            # 初始化或清理历史记录
            if client_id not in request_history:
                request_history[client_id] = []

            # 移除超出时间窗口的请求
            request_history[client_id] = [
                timestamp for timestamp in request_history[client_id]
                if now - timestamp < window_seconds
            ]

            # 检查是否超过限制
            if len(request_history[client_id]) >= max_requests:
                logger.warning(f"速率限制触发: {client_id} ({len(request_history[client_id])} 请求)")
                return jsonify({
                    'error': f'请求过于频繁,请在 {window_seconds} 秒后重试'
                }), 429

            # 记录本次请求
            request_history[client_id].append(now)

            return f(*args, **kwargs)

        return decorated_function
    return decorator
