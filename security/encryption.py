"""
密钥加密存储模块
提供对敏感API密钥的加密存储功能
"""
import os
import json
import base64
from pathlib import Path
from typing import Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from logger import setup_logger

logger = setup_logger("security.encryption")


class KeyEncryption:
    """密钥加密管理器"""

    def __init__(self, master_password: Optional[str] = None, key_file: str = ".keystore"):
        """
        初始化密钥加密管理器

        Args:
            master_password: 主密码,用于派生加密密钥
            key_file: 加密密钥存储文件路径
        """
        self.key_file = Path(key_file)
        self.master_password = master_password or os.getenv('MASTER_PASSWORD')

        if not self.master_password:
            raise ValueError("必须提供主密码或设置MASTER_PASSWORD环境变量")

        self.encryption_key = self._derive_key(self.master_password)
        self.cipher = Fernet(self.encryption_key)

    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """
        从密码派生加密密钥

        Args:
            password: 主密码
            salt: 盐值(可选)

        Returns:
            Base64编码的加密密钥
        """
        if salt is None:
            # 使用固定盐值或从配置读取
            salt = b'backpack-mm-salt'  # 生产环境应使用随机生成并安全存储的盐值

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_credentials(self, credentials: Dict[str, str]) -> None:
        """
        加密并保存凭证

        Args:
            credentials: 包含API密钥的字典
                {
                    'exchange': 'backpack',
                    'api_key': 'xxx',
                    'secret_key': 'xxx'
                }
        """
        try:
            # 读取现有密钥库
            existing_data = {}
            if self.key_file.exists():
                existing_data = self.load_all_credentials()

            # 更新或添加新凭证
            exchange = credentials.get('exchange', 'default')
            existing_data[exchange] = credentials

            # 加密整个数据
            json_data = json.dumps(existing_data)
            encrypted_data = self.cipher.encrypt(json_data.encode())

            # 保存到文件
            with open(self.key_file, 'wb') as f:
                f.write(encrypted_data)

            # 设置文件权限为仅所有者可读写
            os.chmod(self.key_file, 0o600)

            logger.info(f"成功加密并保存 {exchange} 的凭证")

        except Exception as e:
            logger.error(f"加密凭证失败: {e}")
            raise

    def load_all_credentials(self) -> Dict[str, Dict[str, str]]:
        """
        加载所有加密的凭证

        Returns:
            所有交易所的凭证字典
        """
        try:
            if not self.key_file.exists():
                logger.warning(f"密钥库文件不存在: {self.key_file}")
                return {}

            with open(self.key_file, 'rb') as f:
                encrypted_data = f.read()

            # 解密数据
            decrypted_data = self.cipher.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())

            return credentials

        except Exception as e:
            logger.error(f"解密凭证失败: {e}")
            raise

    def load_credentials(self, exchange: str) -> Optional[Dict[str, str]]:
        """
        加载特定交易所的凭证

        Args:
            exchange: 交易所名称

        Returns:
            交易所凭证或None
        """
        all_creds = self.load_all_credentials()
        return all_creds.get(exchange)

    def delete_credentials(self, exchange: str) -> bool:
        """
        删除特定交易所的凭证

        Args:
            exchange: 交易所名称

        Returns:
            是否成功删除
        """
        try:
            all_creds = self.load_all_credentials()
            if exchange in all_creds:
                del all_creds[exchange]

                # 重新加密并保存
                json_data = json.dumps(all_creds)
                encrypted_data = self.cipher.encrypt(json_data.encode())

                with open(self.key_file, 'wb') as f:
                    f.write(encrypted_data)

                logger.info(f"成功删除 {exchange} 的凭证")
                return True
            else:
                logger.warning(f"未找到 {exchange} 的凭证")
                return False

        except Exception as e:
            logger.error(f"删除凭证失败: {e}")
            return False


def migrate_env_to_encrypted(master_password: str, key_file: str = ".keystore") -> None:
    """
    将环境变量中的密钥迁移到加密存储

    Args:
        master_password: 主密码
        key_file: 密钥库文件路径
    """
    encryptor = KeyEncryption(master_password, key_file)

    exchanges = {
        'backpack': {
            'api_key': os.getenv('BACKPACK_KEY'),
            'secret_key': os.getenv('BACKPACK_SECRET'),
        },
        'aster': {
            'api_key': os.getenv('ASTER_API_KEY'),
            'secret_key': os.getenv('ASTER_SECRET_KEY'),
        },
        'paradex': {
            'account_address': os.getenv('PARADEX_ACCOUNT_ADDRESS'),
            'private_key': os.getenv('PARADEX_PRIVATE_KEY'),
        },
        'lighter': {
            'private_key': os.getenv('LIGHTER_PRIVATE_KEY'),
            'api_key_index': os.getenv('LIGHTER_API_KEY_INDEX'),
            'account_index': os.getenv('LIGHTER_ACCOUNT_INDEX'),
        }
    }

    for exchange, creds in exchanges.items():
        # 过滤掉空值
        filtered_creds = {k: v for k, v in creds.items() if v}
        if filtered_creds:
            filtered_creds['exchange'] = exchange
            encryptor.encrypt_credentials(filtered_creds)
            logger.info(f"已迁移 {exchange} 的凭证到加密存储")

    logger.info("密钥迁移完成")
    logger.warning("建议从.env文件中删除明文密钥")


if __name__ == '__main__':
    # 测试和迁移工具
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        # 从环境变量迁移
        from dotenv import load_dotenv
        load_dotenv()

        master_pwd = input("请输入主密码(用于加密密钥): ")
        migrate_env_to_encrypted(master_pwd)
        print("迁移完成!")
    else:
        print("用法: python encryption.py migrate")
