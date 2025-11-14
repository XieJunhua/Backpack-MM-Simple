# 永续做市策略深度解析

## 🤔 核心问题：策略如何决定做多还是做空？

你的命令：
```bash
python run.py --exchange backpack --market-type perp --symbol SOL_USDC_PERP \
  --spread 0.01 --quantity 0.1 --max-orders 2 \
  --target-position 0 --max-position 5 --position-threshold 2 \
  --inventory-skew 0 --stop-loss -1 --take-profit 5 \
  --duration 3600 --interval 10
```

**确实没有明确指定做多还是做空！**

---

## 💡 答案：策略是**双向做市**，被动形成持仓

### 工作原理

```
永续做市策略 ≠ 主动做多/做空
永续做市策略 = 双向挂单 + 被动成交 + 动态持仓管理
```

### 详细流程

#### 第1步：同时挂买单和卖单

```python
# strategies/market_maker.py:1624-1755

def place_limit_orders(self):
    """下限价单"""

    # 计算买入价格（低于市场价）
    buy_prices = [
        current_price * (1 - spread),
        current_price * (1 - spread * 2),
        ...
    ]

    # 计算卖出价格（高于市场价）
    sell_prices = [
        current_price * (1 + spread),
        current_price * (1 + spread * 2),
        ...
    ]

    # 同时下买单和卖单
    for price in buy_prices:
        下买单(price, quantity)

    for price in sell_prices:
        下卖单(price, quantity)
```

**关键点**：
- ✅ 买单和卖单**同时存在**
- ✅ 不是主动选择方向，而是**等待市场成交**
- ✅ 哪边先成交，就先形成那个方向的持仓

---

#### 第2步：被动成交形成持仓

```
时刻 T0: 当前价格 100 USDC
  挂买单: 99 USDC × 0.1 SOL
  挂卖单: 101 USDC × 0.1 SOL
  当前持仓: 0 SOL

场景A: 价格下跌，买单先成交
  时刻 T1: 价格跌到 99 USDC
  → 买单成交: +0.1 SOL @ 99 USDC
  → 当前持仓: +0.1 SOL（做多）

场景B: 价格上涨，卖单先成交
  时刻 T1: 价格涨到 101 USDC
  → 卖单成交: -0.1 SOL @ 101 USDC
  → 当前持仓: -0.1 SOL（做空）
```

**关键点**：
- ❌ 策略**不主动选择**做多还是做空
- ✅ 由**市场价格波动**决定哪边先成交
- ✅ 成交后**被动形成**多头或空头持仓

---

#### 第3步：动态调整倾斜度

这里就是 `target_position` 和 `inventory_skew` 发挥作用的地方！

##### `target_position=0` 的含义

```python
# strategies/perp_market_maker.py:78
self.target_position = abs(target_position)  # 0
```

**含义**：
- ✅ 策略希望持仓接近 **0**（中性）
- ✅ 当持仓偏离0时，调整订单倾斜度
- ✅ **不是强制平仓**，而是通过调整报价引导持仓回归

##### `inventory_skew=0` 的含义

```python
# strategies/perp_market_maker.py:81
self.inventory_skew = max(0.0, min(1.0, inventory_skew))  # 0.0
```

**含义**：
- ✅ `inventory_skew=0`：**不启用**库存偏移调整
- ✅ 订单不会因为持仓而倾斜
- ✅ 买单和卖单的价差保持对称

---

### 实际运行示例（你的参数）

```bash
--target-position 0      # 目标持仓 0
--inventory-skew 0       # 不倾斜订单
--max-position 5         # 最大允许持仓 5 SOL
--position-threshold 2   # 超过2 SOL触发调整
```

#### 场景1：买单先成交

```
时刻 T0: 价格 100 USDC
  挂单: 买@99, 卖@101
  持仓: 0 SOL

时刻 T1: 价格跌到 99 USDC，买单成交
  成交: +0.1 SOL @ 99 USDC
  持仓: +0.1 SOL（做多）

时刻 T2: 继续挂单（inventory_skew=0，不调整）
  挂单: 买@98, 卖@100
  持仓: +0.1 SOL

时刻 T3: 价格涨到 100 USDC，卖单成交
  成交: -0.1 SOL @ 100 USDC
  持仓: 0 SOL ✅ 回到平仓
  盈利: (100 - 99) * 0.1 = 0.1 USDC
```

#### 场景2：持仓超过阈值

```
假设连续多次买单成交:
  持仓: +2.5 SOL（超过 position_threshold=2）

此时策略会：
  ❌ 不会立即平仓（因为 inventory_skew=0）
  ❌ 不会调整订单倾斜度
  ✅ 继续双向挂单，等待卖单成交
  ⚠️ 如果持仓达到 max_position=5，可能触发风控
```

#### 场景3：如果启用 inventory_skew

```bash
# 假设改为 --inventory-skew 0.5
```

```
持仓: +2.5 SOL（多头）
目标: 0 SOL
偏离: +2.5 SOL

策略会调整订单:
  买单价格下调: 99 → 98.5（减少买入概率）
  卖单价格上调: 101 → 101.5（增加卖出概率）

目的: 通过调整报价，引导持仓回归0
```

---

## 🎯 参数详解

### 1. `target_position` (目标持仓)

```bash
--target-position 0    # 希望持仓接近0（中性）
--target-position 1    # 希望持仓接近±1 SOL
--target-position 2    # 希望持仓接近±2 SOL
```

**作用**：
- 不是强制持仓量
- 是策略**倾向的持仓水平**
- 配合 `inventory_skew` 引导持仓

**注意**：
```python
self.target_position = abs(target_position)  # 取绝对值
```
- ✅ `target_position=1` 表示持仓接近 ±1
- ❌ 不能指定方向（+1 或 -1）
- ✅ 方向由市场成交决定

---

### 2. `inventory_skew` (库存偏移)

```bash
--inventory-skew 0      # 不调整（买卖对称）
--inventory-skew 0.5    # 中等调整
--inventory-skew 1.0    # 最大调整
```

**作用**：
- 当持仓偏离 `target_position` 时
- 调整买卖单价格的倾斜度
- 引导持仓回归目标

**计算公式**（简化）：
```python
if current_position > target_position:
    # 持仓过多，想卖出
    买单价格 -= 偏移量 * inventory_skew
    卖单价格 += 偏移量 * inventory_skew

elif current_position < target_position:
    # 持仓不足，想买入
    买单价格 += 偏移量 * inventory_skew
    卖单价格 -= 偏移量 * inventory_skew
```

---

### 3. `max_position` (最大持仓)

```bash
--max-position 5    # 最大允许持仓 ±5 SOL
```

**作用**：
- 硬限制，防止持仓过大
- 超过此值可能触发风控或拒绝开仓

---

### 4. `position_threshold` (调整阈值)

```bash
--position-threshold 2    # 持仓偏离超过2才调整
```

**作用**：
- 只有当 `|current_position - target_position| > threshold` 时
- 才触发订单倾斜调整
- 避免频繁调整

---

## 🔄 完整运行流程图

```
┌─────────────────────────────────────────┐
│  初始状态: 持仓 0 SOL                    │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  同时挂买单和卖单                        │
│  买单: 99 USDC × 0.1 SOL (2个)          │
│  卖单: 101 USDC × 0.1 SOL (2个)         │
└─────────────────────────────────────────┘
              ↓
        市场价格波动
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
买单成交           卖单成交
持仓 +0.1 SOL      持仓 -0.1 SOL
(做多)             (做空)
    ↓                   ↓
检查持仓偏离
    ↓
|持仓 - 目标| > 阈值？
    ↓
  是 → 调整订单倾斜度（如果 inventory_skew > 0）
  否 → 继续双向挂单
    ↓
取消旧订单，挂新订单
    ↓
等待下一轮成交
```

---

## ❓ 常见问题

### Q1: 如何让策略只做多？

**答**：永续做市策略不支持纯做多/做空。

如果你想纯做多：
```bash
# 方案1: 使用市价单直接开仓
# 然后用其他策略管理

# 方案2: 修改代码，只挂买单
# （不推荐，失去做市的意义）
```

---

### Q2: `target_position=0` 是否会强制平仓？

**答**：❌ 不会！

- `target_position` 只是**目标**，不是强制
- 只有配合 `inventory_skew > 0` 才会调整订单
- 即使 `inventory_skew=0`，策略也不会主动平仓

如果想强制平仓：
- 需要依靠 `stop_loss` 或 `take_profit`
- 或者手动调用 `close_position()`

---

### Q3: 持仓会无限增大吗？

**答**：有保护机制

1. **`max_position` 限制**：
   - 持仓达到 `max_position` 时，可能拒绝新订单

2. **`stop_loss` 和 `take_profit`**：
   - 未实现盈亏达到阈值时，自动平仓

3. **资金限制**：
   - 资金不足时，无法继续开仓

---

### Q4: 为什么我的参数是 `target_position=0` 但还是有持仓？

**答**：这是正常的！

```
target_position=0 的含义:
  ✅ 策略"希望"持仓接近0
  ✅ 不是"强制"持仓为0

实际持仓:
  ✅ 由市场成交决定
  ✅ 可能是 +2 SOL（多头）
  ✅ 可能是 -1.5 SOL（空头）
  ✅ 可能是 0 SOL（平仓）
```

如果你想更积极地维持0持仓：
```bash
--inventory-skew 0.8    # 增大调整力度
--position-threshold 0.5 # 降低触发阈值
```

---

### Q5: 如何配置更激进的做市？

```bash
# 激进配置（追求高成交量）
python run.py \
  --spread 0.005 \          # 更小价差
  --quantity 0.2 \          # 更大数量
  --max-orders 5 \          # 更多订单
  --target-position 2 \     # 允许更大持仓
  --max-position 10 \       # 更大最大持仓
  --inventory-skew 0.3      # 温和调整
```

---

### Q6: 如何配置保守的做市？

```bash
# 保守配置（控制风险）
python run.py \
  --spread 0.02 \           # 更大价差
  --quantity 0.05 \         # 更小数量
  --max-orders 1 \          # 最少订单
  --target-position 0 \     # 希望中性
  --max-position 2 \        # 严格限制持仓
  --inventory-skew 0.8 \    # 强力调整
  --stop-loss 50 \          # 严格止损
  --take-profit 100         # 保守止盈
```

---

## 📊 推荐配置

### 配置1：中性做市（最安全）

```bash
python run.py \
  --exchange backpack \
  --market-type perp \
  --symbol SOL_USDC_PERP \
  --spread 0.01 \
  --quantity 0.1 \
  --max-orders 2 \
  --target-position 0 \      # 目标中性
  --max-position 3 \         # 限制持仓
  --position-threshold 1 \   # 敏感调整
  --inventory-skew 0.7 \     # 强力引导
  --stop-loss 100 \
  --take-profit 200 \
  --duration 3600 \
  --interval 10
```

**特点**：
- ✅ 追求持仓接近0
- ✅ 依靠价差盈利
- ✅ 风险相对较低

---

### 配置2：允许持仓（平衡）

```bash
python run.py \
  --exchange backpack \
  --market-type perp \
  --symbol SOL_USDC_PERP \
  --spread 0.01 \
  --quantity 0.1 \
  --max-orders 3 \
  --target-position 1 \      # 允许小幅持仓
  --max-position 5 \
  --position-threshold 2 \
  --inventory-skew 0.3 \     # 温和调整
  --stop-loss 200 \
  --take-profit 400 \
  --duration 3600 \
  --interval 10
```

**特点**：
- ✅ 允许持仓波动
- ✅ 价差 + 方向性收益
- ⚠️ 风险适中

---

### 配置3：你当前的配置（问题分析）

```bash
--target-position 0       # ✅ 希望中性
--inventory-skew 0        # ❌ 不调整！
--position-threshold 2    # ⚠️ 阈值较大
```

**问题**：
- `inventory_skew=0` 意味着**完全不调整订单倾斜度**
- 即使持仓偏离很大，订单依然对称
- 持仓可能长时间偏离目标

**建议修改**：
```bash
--inventory-skew 0.5      # 启用调整
--position-threshold 1    # 降低阈值
```

---

## 🎓 总结

### 关键要点

1. **永续做市 ≠ 主动做多/做空**
   - 双向挂单，被动成交
   - 方向由市场决定

2. **`target_position` 不是强制**
   - 只是"目标"，不是"命令"
   - 需要配合 `inventory_skew` 才能引导

3. **`inventory_skew=0` 意味着不调整**
   - 买卖单永远对称
   - 持仓完全随机游走

4. **想要控制持仓，必须调整参数**
   - 增大 `inventory_skew`
   - 降低 `position_threshold`
   - 或使用止损止盈强制平仓

---

**版本**: 1.0
**最后更新**: 2025-11-14
**作者**: Claude Code
