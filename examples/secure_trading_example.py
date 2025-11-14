"""
安全交易示例
演示如何使用加密存储、Web认证和滑点保护功能
"""
import os
import sys

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security import KeyEncryption
from strategies.perp_market_maker import PerpetualMarketMaker
from logger import setup_logger

logger = setup_logger("secure_example")


def example_1_encrypted_credentials():
    """示例1: 使用加密存储的凭证"""
    logger.info("=== 示例1: 使用加密存储 ===")

    # 从加密存储加载凭证
    encryptor = KeyEncryption()  # 自动从环境变量读取MASTER_PASSWORD

    try:
        # 加载Backpack凭证
        creds = encryptor.load_credentials('backpack')
        api_key = creds['api_key']
        secret_key = creds['secret_key']

        logger.info("成功从加密存储加载Backpack凭证")
        logger.info(f"API Key前缀: {api_key[:8]}...")

        return api_key, secret_key

    except Exception as e:
        logger.error(f"加载凭证失败: {e}")
        # 回退到环境变量
        logger.warning("回退使用环境变量")
        return os.getenv('BACKPACK_KEY'), os.getenv('BACKPACK_SECRET')


def example_2_slippage_protection():
    """示例2: 启用滑点保护的永续做市"""
    logger.info("=== 示例2: 启用滑点保护 ===")

    # 加载凭证
    api_key, secret_key = example_1_encrypted_credentials()

    if not api_key or not secret_key:
        logger.error("缺少API凭证,请先配置")
        return

    # 创建策略 (启用滑点保护)
    strategy = PerpetualMarketMaker(
        api_key=api_key,
        secret_key=secret_key,
        symbol='SOL_USDC',
        base_spread_percentage=0.5,  # 0.5%价差
        order_quantity=0.1,  # 每单0.1 SOL

        # 永续合约参数
        target_position=1.0,  # 目标持仓1 SOL
        max_position=5.0,     # 最大持仓5 SOL
        position_threshold=0.1,  # 0.1 SOL阈值
        inventory_skew=0.002,  # 0.2%库存偏移

        # 止损止盈
        stop_loss=100.0,      # 止损100 USDC
        take_profit=200.0,    # 止盈200 USDC

        # 滑点保护 ⭐
        max_slippage_bps=50,  # 0.5%最大滑点
        enable_slippage_protection=True,

        # 其他
        exchange='backpack',
        enable_database=True
    )

    logger.info("策略创建成功,配置如下:")
    logger.info(f"  交易对: {strategy.symbol}")
    logger.info(f"  价差: {strategy.base_spread_percentage}%")
    logger.info(f"  目标持仓: {strategy.target_position}")
    logger.info(f"  滑点保护: {'启用' if strategy.slippage_protection else '禁用'}")

    # 运行策略 (1小时,每60秒调整一次)
    try:
        logger.info("开始运行策略...")
        strategy.run(duration_seconds=3600, interval_seconds=60)
    except KeyboardInterrupt:
        logger.info("用户中断,正在停止...")
        strategy.stop()
    except Exception as e:
        logger.error(f"策略运行错误: {e}")
        strategy.stop()


def example_3_web_authentication():
    """示例3: Web API认证使用"""
    logger.info("=== 示例3: Web API认证 ===")

    import requests

    # API基础URL
    base_url = "http://localhost:5000"

    # 步骤1: 登录
    login_data = {
        "username": "admin",
        "password": os.getenv('ADMIN_PASSWORD', 'admin')
    }

    try:
        logger.info("正在登录...")
        response = requests.post(
            f"{base_url}/api/login",
            json=login_data,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            token = data['token']
            logger.info("登录成功!")
            logger.info(f"Token前缀: {token[:16]}...")

            # 步骤2: 使用Token启动策略
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            start_config = {
                "exchange": "backpack",
                "symbol": "SOL_USDC",
                "spread": 0.5,
                "market_type": "perp",
                "target_position": 1.0,
                "max_position": 5.0,
                "max_slippage_bps": 50,
                "stop_loss": 100,
                "take_profit": 200
            }

            logger.info("正在启动策略...")
            response = requests.post(
                f"{base_url}/api/start",
                json=start_config,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("策略启动成功!")
                logger.info(response.json())
            else:
                logger.error(f"启动失败: {response.text}")

        else:
            logger.error(f"登录失败: {response.text}")

    except requests.exceptions.ConnectionError:
        logger.error("无法连接到Web服务器,请先启动: python run.py --mode web")
    except Exception as e:
        logger.error(f"请求错误: {e}")


def example_4_add_new_credentials():
    """示例4: 添加新的交易所凭证到加密存储"""
    logger.info("=== 示例4: 添加新凭证 ===")

    encryptor = KeyEncryption()

    # 添加新交易所凭证
    new_creds = {
        'exchange': 'binance',
        'api_key': 'your-binance-key',
        'secret_key': 'your-binance-secret'
    }

    try:
        encryptor.encrypt_credentials(new_creds)
        logger.info(f"成功添加 {new_creds['exchange']} 的凭证到加密存储")

        # 验证
        loaded = encryptor.load_credentials('binance')
        logger.info(f"验证成功: {list(loaded.keys())}")

    except Exception as e:
        logger.error(f"添加凭证失败: {e}")


def example_5_slippage_monitoring():
    """示例5: 滑点保护监控和动态调整"""
    logger.info("=== 示例5: 滑点监控 ===")

    from utils.slippage_protection import SlippageProtection

    # 创建滑点保护实例
    slippage = SlippageProtection(
        max_slippage_bps=50,
        enable_protection=True
    )

    # 模拟价格检查
    reference_price = 145.50
    execution_prices = [145.60, 145.75, 146.00, 146.50]

    logger.info(f"参考价格: {reference_price}")
    logger.info(f"最大滑点: {slippage.max_slippage_bps}bp ({slippage.max_slippage_ratio*100:.2f}%)")

    for exec_price in execution_prices:
        passed, deviation_pct, msg = slippage.check_price_deviation(
            reference_price=reference_price,
            execution_price=exec_price,
            side='buy'
        )

        status = "✅ 通过" if passed else "❌ 拒绝"
        logger.info(f"{status} | 执行价 {exec_price:.2f} | 偏离 {deviation_pct:.3f}% | {msg}")

    # 动态调整滑点阈值
    logger.info("\n调整滑点阈值到100bp...")
    slippage.set_max_slippage(100)

    # 重新检查
    exec_price = 146.50
    passed, deviation_pct, msg = slippage.check_price_deviation(
        reference_price=reference_price,
        execution_price=exec_price,
        side='buy'
    )
    status = "✅ 通过" if passed else "❌ 拒绝"
    logger.info(f"{status} | 执行价 {exec_price:.2f} | 偏离 {deviation_pct:.3f}% | {msg}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Backpack-MM-Simple 安全功能示例")
    print("="*60 + "\n")

    # 检查必要的环境变量
    if not os.getenv('MASTER_PASSWORD'):
        print("⚠️  警告: 未设置 MASTER_PASSWORD 环境变量")
        print("请先设置: export MASTER_PASSWORD='your-password'\n")

    examples = {
        '1': ('使用加密存储的凭证', example_1_encrypted_credentials),
        '2': ('启用滑点保护的永续做市', example_2_slippage_protection),
        '3': ('Web API认证使用', example_3_web_authentication),
        '4': ('添加新凭证到加密存储', example_4_add_new_credentials),
        '5': ('滑点保护监控和调整', example_5_slippage_monitoring),
    }

    print("可用示例:")
    for key, (desc, _) in examples.items():
        print(f"  {key}. {desc}")

    print("\n输入示例编号 (或 'all' 运行所有示例):")
    choice = input("> ").strip()

    if choice == 'all':
        for key, (desc, func) in examples.items():
            print(f"\n{'='*60}")
            print(f"运行示例 {key}: {desc}")
            print('='*60)
            try:
                func()
            except Exception as e:
                logger.error(f"示例 {key} 执行出错: {e}")
                import traceback
                traceback.print_exc()
    elif choice in examples:
        desc, func = examples[choice]
        print(f"\n运行示例: {desc}")
        try:
            func()
        except Exception as e:
            logger.error(f"执行出错: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("无效的选择")


if __name__ == '__main__':
    main()
