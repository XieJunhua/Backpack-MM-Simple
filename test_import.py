#!/usr/bin/env python3
"""
测试加密模块导入是否正确
"""

try:
    print("测试 cryptography 导入...")
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    print("✅ cryptography 导入成功")

    print("\n测试 PBKDF2HMAC 使用...")
    import base64

    password = "test_password"
    salt = b'test_salt_12345'

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    print(f"✅ PBKDF2HMAC 工作正常")
    print(f"   生成的密钥: {key[:32]}...")

    print("\n测试 Fernet 加密...")
    cipher = Fernet(key)
    test_data = b"Hello, World!"
    encrypted = cipher.encrypt(test_data)
    decrypted = cipher.decrypt(encrypted)

    assert decrypted == test_data
    print("✅ Fernet 加密解密正常")

    print("\n🎉 所有测试通过！")

except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("\n请安装依赖:")
    print("  pip install cryptography")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
