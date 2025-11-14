#!/usr/bin/env python3
"""
测试安全模块导入（无需其他依赖）
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("测试安全模块导入修复")
print("=" * 60)

# 测试 1: 直接导入 encryption 模块
print("\n[测试 1] 导入 encryption 模块...")
try:
    from security.encryption import KeyEncryption
    print("✅ KeyEncryption 导入成功")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 2: 测试加密功能
print("\n[测试 2] 测试加密功能...")
try:
    # 创建临时密钥加密器
    encryptor = KeyEncryption(master_password="test_password_123", key_file=".test_keystore")
    print("✅ KeyEncryption 实例创建成功")

    # 测试加密
    test_creds = {
        'exchange': 'test',
        'api_key': 'test_key',
        'secret_key': 'test_secret'
    }
    encryptor.encrypt_credentials(test_creds)
    print("✅ 凭证加密成功")

    # 测试解密
    loaded = encryptor.load_credentials('test')
    assert loaded['api_key'] == 'test_key'
    print("✅ 凭证解密成功")

    # 清理测试文件
    if os.path.exists('.test_keystore'):
        os.remove('.test_keystore')
    print("✅ 测试文件清理完成")

except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 3: 导入滑点保护
print("\n[测试 3] 导入滑点保护模块...")
try:
    from utils.slippage_protection import SlippageProtection
    print("✅ SlippageProtection 导入成功")

    # 测试滑点保护功能
    slippage = SlippageProtection(max_slippage_bps=50, enable_protection=True)
    passed, deviation, msg = slippage.check_price_deviation(
        reference_price=100.0,
        execution_price=100.3,
        side='buy'
    )
    print(f"✅ 滑点检查功能正常: {msg}")

except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 4: 导入认证模块（可能因为缺少 Flask 而失败）
print("\n[测试 4] 导入认证模块...")
try:
    from security.auth import TokenAuth
    print("✅ TokenAuth 导入成功")

    # 测试 TokenAuth 功能
    auth = TokenAuth(token_expiry_hours=24)
    print("✅ TokenAuth 实例创建成功")

except ImportError as e:
    if 'flask' in str(e).lower():
        print("⚠️  跳过: Flask 未安装（在服务器环境中应该可用）")
    else:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
print("\n提示: 如果某些测试失败，请确保:")
print("  1. 在项目根目录运行此脚本")
print("  2. 已安装必要的依赖: pip install cryptography flask")
print("  3. Python 版本 >= 3.7")
