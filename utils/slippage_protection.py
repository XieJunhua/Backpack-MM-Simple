"""
滑点保护模块
提供价格偏离检测和滑点保护功能
"""
from typing import Optional, Tuple
from logger import setup_logger

logger = setup_logger("utils.slippage_protection")


class SlippageProtection:
    """滑点保护管理器"""

    def __init__(
        self,
        max_slippage_bps: int = 50,  # 最大滑点(基点,1bps=0.01%)
        enable_protection: bool = True
    ):
        """
        初始化滑点保护

        Args:
            max_slippage_bps: 最大允许滑点(基点),默认50bp=0.5%
            enable_protection: 是否启用保护
        """
        self.max_slippage_bps = max_slippage_bps
        self.max_slippage_ratio = max_slippage_bps / 10000.0  # 转换为小数
        self.enable_protection = enable_protection

        if enable_protection:
            logger.info(f"滑点保护已启用: 最大滑点 {max_slippage_bps}bp ({self.max_slippage_ratio*100:.2f}%)")
        else:
            logger.warning("滑点保护已禁用")

    def check_price_deviation(
        self,
        reference_price: float,
        execution_price: float,
        side: str = 'buy'
    ) -> Tuple[bool, float, str]:
        """
        检查价格偏离是否超过允许范围

        Args:
            reference_price: 参考价格(如中间价)
            execution_price: 执行价格
            side: 交易方向 'buy' 或 'sell'

        Returns:
            (是否通过检查, 偏离百分比, 消息)
        """
        if not self.enable_protection:
            return True, 0.0, "滑点保护已禁用"

        if reference_price <= 0:
            logger.error(f"参考价格无效: {reference_price}")
            return False, 0.0, "参考价格无效"

        # 计算价格偏离
        # 买入时,执行价高于参考价为不利滑点
        # 卖出时,执行价低于参考价为不利滑点
        if side.lower() in ['buy', 'bid']:
            deviation = (execution_price - reference_price) / reference_price
        else:  # sell/ask
            deviation = (reference_price - execution_price) / reference_price

        deviation_pct = deviation * 100

        # 检查是否超过允许的滑点
        if abs(deviation) > self.max_slippage_ratio:
            msg = (
                f"价格偏离过大: {deviation_pct:.3f}% "
                f"(限制: {self.max_slippage_ratio*100:.2f}%) "
                f"参考价: {reference_price:.6f}, "
                f"执行价: {execution_price:.6f}, "
                f"方向: {side}"
            )
            logger.warning(msg)
            return False, deviation_pct, msg

        logger.debug(
            f"价格偏离检查通过: {deviation_pct:.3f}% "
            f"(参考: {reference_price:.6f}, 执行: {execution_price:.6f}, {side})"
        )
        return True, deviation_pct, "价格偏离在允许范围内"

    def calculate_limit_price(
        self,
        reference_price: float,
        side: str,
        slippage_bps: Optional[int] = None
    ) -> float:
        """
        根据滑点保护计算限价单价格

        Args:
            reference_price: 参考价格
            side: 交易方向 'buy' 或 'sell'
            slippage_bps: 自定义滑点(可选),不提供则使用默认值

        Returns:
            限价单价格
        """
        if slippage_bps is None:
            slippage_bps = self.max_slippage_bps

        slippage_ratio = slippage_bps / 10000.0

        if side.lower() in ['buy', 'bid']:
            # 买入时,价格上浮以允许一定滑点
            limit_price = reference_price * (1 + slippage_ratio)
        else:  # sell/ask
            # 卖出时,价格下调以允许一定滑点
            limit_price = reference_price * (1 - slippage_ratio)

        logger.debug(
            f"计算限价: {side} {limit_price:.6f} "
            f"(参考: {reference_price:.6f}, 滑点: {slippage_bps}bp)"
        )
        return limit_price

    def check_orderbook_liquidity(
        self,
        bids: list,
        asks: list,
        reference_price: float,
        target_quantity: float,
        side: str
    ) -> Tuple[bool, float, str]:
        """
        检查订单簿流动性和预期滑点

        Args:
            bids: 买单列表 [(price, quantity), ...]
            asks: 卖单列表 [(price, quantity), ...]
            reference_price: 参考价格
            target_quantity: 目标交易量
            side: 交易方向

        Returns:
            (是否通过检查, 预期滑点%, 消息)
        """
        if not self.enable_protection:
            return True, 0.0, "滑点保护已禁用"

        if side.lower() in ['buy', 'bid']:
            # 买入时检查卖单深度
            orderbook = asks
            is_buy = True
        else:
            # 卖出时检查买单深度
            orderbook = bids
            is_buy = False

        if not orderbook:
            return False, 0.0, "订单簿为空"

        # 计算执行目标数量所需的平均价格
        remaining = target_quantity
        total_cost = 0.0
        executed = 0.0

        for price, quantity in orderbook:
            price = float(price)
            quantity = float(quantity)

            if remaining <= 0:
                break

            fill_qty = min(remaining, quantity)
            total_cost += price * fill_qty
            executed += fill_qty
            remaining -= fill_qty

        if executed < target_quantity:
            shortage_pct = (1 - executed / target_quantity) * 100
            msg = f"订单簿深度不足: 只能成交 {executed}/{target_quantity} ({shortage_pct:.1f}%缺口)"
            logger.warning(msg)
            return False, 0.0, msg

        # 计算平均成交价
        avg_price = total_cost / executed

        # 计算预期滑点
        if is_buy:
            expected_slippage = (avg_price - reference_price) / reference_price
        else:
            expected_slippage = (reference_price - avg_price) / reference_price

        expected_slippage_pct = expected_slippage * 100

        # 检查预期滑点是否超过限制
        if abs(expected_slippage) > self.max_slippage_ratio:
            msg = (
                f"预期滑点过大: {expected_slippage_pct:.3f}% "
                f"(限制: {self.max_slippage_ratio*100:.2f}%) "
                f"平均价: {avg_price:.6f}, 参考价: {reference_price:.6f}"
            )
            logger.warning(msg)
            return False, expected_slippage_pct, msg

        msg = f"流动性充足,预期滑点: {expected_slippage_pct:.3f}%"
        logger.debug(msg)
        return True, expected_slippage_pct, msg

    def set_max_slippage(self, max_slippage_bps: int):
        """
        动态调整最大滑点

        Args:
            max_slippage_bps: 新的最大滑点(基点)
        """
        old_bps = self.max_slippage_bps
        self.max_slippage_bps = max_slippage_bps
        self.max_slippage_ratio = max_slippage_bps / 10000.0
        logger.info(
            f"最大滑点已更新: {old_bps}bp -> {max_slippage_bps}bp "
            f"({self.max_slippage_ratio*100:.2f}%)"
        )

    def enable(self):
        """启用滑点保护"""
        self.enable_protection = True
        logger.info("滑点保护已启用")

    def disable(self):
        """禁用滑点保护"""
        self.enable_protection = False
        logger.warning("滑点保护已禁用")


# 辅助函数
def validate_market_order_price(
    current_price: float,
    bid_price: float,
    ask_price: float,
    side: str,
    max_spread_bps: int = 100
) -> Tuple[bool, str]:
    """
    验证市价单价格合理性

    Args:
        current_price: 当前参考价格
        bid_price: 最优买价
        ask_price: 最优卖价
        side: 交易方向
        max_spread_bps: 最大允许价差(基点)

    Returns:
        (是否通过, 消息)
    """
    if current_price <= 0 or bid_price <= 0 or ask_price <= 0:
        return False, "价格数据无效"

    # 检查价差是否异常
    spread = ask_price - bid_price
    spread_ratio = spread / current_price
    spread_bps = spread_ratio * 10000

    if spread_bps > max_spread_bps:
        msg = f"价差过大: {spread_bps:.1f}bp (限制: {max_spread_bps}bp)"
        logger.warning(msg)
        return False, msg

    # 检查最优价格与参考价的偏离
    if side.lower() in ['buy', 'bid']:
        execution_price = ask_price  # 买入吃卖单
        deviation = (execution_price - current_price) / current_price
    else:
        execution_price = bid_price  # 卖出吃买单
        deviation = (current_price - execution_price) / current_price

    deviation_pct = abs(deviation) * 100

    if deviation_pct > 5:  # 偏离超过5%
        msg = f"执行价偏离参考价过大: {deviation_pct:.2f}%"
        logger.warning(msg)
        return False, msg

    return True, f"市价单价格验证通过 (价差: {spread_bps:.1f}bp)"
