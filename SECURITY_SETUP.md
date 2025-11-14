# 安全功能配置指南

本文档提供了详细的步骤来配置和使用新添加的安全功能。

## 目录

- [1. 安装依赖](#1-安装依赖)
- [2. 密钥加密存储](#2-密钥加密存储)
- [3. Web认证配置](#3-web认证配置)
- [4. 滑点保护设置](#4-滑点保护设置)
- [5. 完整示例](#5-完整示例)
- [6. 故障排除](#6-故障排除)

---

## 1. 安装依赖

### 1.1 安装必要的Python包

```bash
pip install cryptography flask-socketio
```

或者更新 `requirements.txt`:
```txt
cryptography>=41.0.0
PyNaCl>=1.5.0
flask>=2.3.0
flask-socketio>=5.3.0
python-dotenv>=1.0.0
```

然后运行:
```bash
pip install -r requirements.txt
```

---

## 2. 密钥加密存储

### 2.1 迁移现有密钥

**步骤 1**: 设置主密码

```bash
# 临时设置 (仅当前会话有效)
export MASTER_PASSWORD="your-very-strong-password-here"

# 永久设置 (添加到 .env)
echo 'MASTER_PASSWORD=your-very-strong-password-here' >> .env
```

⚠️ **重要**: 主密码必须足够强(至少16个字符,包含大小写字母、数字和特殊字符)

**步骤 2**: 从环境变量迁移密钥

```bash
python security/encryption.py migrate
```

预期输出:
```
已迁移 backpack 的凭证到加密存储
已迁移 aster 的凭证到加密存储
密钥迁移完成
建议从.env文件中删除明文密钥
```

**步骤 3**: 验证加密存储

检查是否生成了 `.keystore` 文件:
```bash
ls -la .keystore
# 应该显示: -rw------- 1 user user ... .keystore
```

**步骤 4**: 删除明文密钥 (可选但推荐)

编辑 `.env` 文件,注释掉或删除明文密钥:
```bash
# 保留主密码
MASTER_PASSWORD=your-very-strong-password-here

# 可以删除这些明文密钥
# BACKPACK_KEY=xxx
# BACKPACK_SECRET=xxx
# ASTER_API_KEY=xxx
# ASTER_SECRET_KEY=xxx
```

### 2.2 在代码中使用加密存储

**方法 1**: 直接使用 (推荐用于新代码)

```python
from security import KeyEncryption

# 初始化
encryptor = KeyEncryption()  # 自动从环境变量读取MASTER_PASSWORD

# 加载凭证
backpack_creds = encryptor.load_credentials('backpack')
api_key = backpack_creds['api_key']
secret_key = backpack_creds['secret_key']

# 使用凭证
from api.bp_client import BackpackClient
client = BackpackClient({
    'api_key': api_key,
    'secret_key': secret_key
})
```

**方法 2**: 修改现有代码

替换:
```python
# 原始代码
api_key = os.getenv('BACKPACK_KEY')
secret_key = os.getenv('BACKPACK_SECRET')
```

为:
```python
# 使用加密存储
from security import KeyEncryption
try:
    encryptor = KeyEncryption()
    creds = encryptor.load_credentials('backpack')
    api_key = creds['api_key']
    secret_key = creds['secret_key']
except Exception as e:
    # 回退到环境变量 (用于向后兼容)
    logger.warning(f"无法从加密存储读取密钥,使用环境变量: {e}")
    api_key = os.getenv('BACKPACK_KEY')
    secret_key = os.getenv('BACKPACK_SECRET')
```

### 2.3 管理加密凭证

**添加新凭证**:
```python
from security import KeyEncryption

encryptor = KeyEncryption()
encryptor.encrypt_credentials({
    'exchange': 'binance',
    'api_key': 'your-binance-key',
    'secret_key': 'your-binance-secret'
})
```

**删除凭证**:
```python
encryptor.delete_credentials('binance')
```

**查看所有凭证** (不显示密钥):
```python
all_creds = encryptor.load_all_credentials()
print(f"已存储的交易所: {list(all_creds.keys())}")
```

---

## 3. Web认证配置

### 3.1 设置管理员账户

编辑 `.env` 文件:
```bash
# Web管理后台认证
ADMIN_USERNAME=admin  # 可选,默认为 admin
ADMIN_PASSWORD=your-admin-password-here  # 必须设置
```

⚠️ **注意**: 如果不设置 `ADMIN_PASSWORD`,系统会生成随机密码并在日志中显示一次。

### 3.2 启动Web服务器

```bash
python web/server.py
```

或使用主程序:
```bash
python run.py --mode web
```

### 3.3 使用API认证

**步骤 1**: 登录获取Token

```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-admin-password"
  }'
```

响应:
```json
{
  "success": true,
  "token": "AbCdEf123456...",
  "message": "登录成功"
}
```

**步骤 2**: 使用Token访问受保护的API

```bash
curl -X POST http://localhost:5000/api/start \
  -H "Authorization: Bearer AbCdEf123456..." \
  -H "Content-Type: application/json" \
  -d '{
    "exchange": "backpack",
    "symbol": "SOL_USDC",
    "spread": 0.5,
    "market_type": "perp"
  }'
```

**步骤 3**: 登出 (可选)

```bash
curl -X POST http://localhost:5000/api/logout \
  -H "Authorization: Bearer AbCdEf123456..."
```

### 3.4 前端集成示例

```javascript
// 登录
async function login(username, password) {
  const response = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();
  if (data.success) {
    // 保存Token到localStorage
    localStorage.setItem('authToken', data.token);
    return true;
  }
  return false;
}

// 使用Token调用API
async function startBot(config) {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/start', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(config)
  });

  return await response.json();
}

// 处理401错误 (Token过期)
fetch('/api/start', { ... })
  .then(response => {
    if (response.status === 401) {
      // Token过期,重新登录
      window.location.href = '/login';
    }
    return response.json();
  });
```

### 3.5 速率限制

以下端点有速率限制:

| 端点 | 限制 | 说明 |
|------|------|------|
| `/api/login` | 5次/分钟 | 防止暴力破解 |
| `/api/start` | 3次/分钟 | 防止频繁启动 |
| `/api/stop` | 5次/分钟 | 允许紧急停止 |

超过限制时返回:
```json
{
  "error": "请求过于频繁,请在 60 秒后重试"
}
```

---

## 4. 滑点保护设置

### 4.1 启用滑点保护

**CLI模式**:
```bash
python run.py \
  --exchange backpack \
  --symbol SOL_USDC \
  --mode perp \
  --spread 0.5 \
  --max-slippage-bps 50
```

**代码模式**:
```python
from strategies.perp_market_maker import PerpetualMarketMaker

strategy = PerpetualMarketMaker(
    api_key=api_key,
    secret_key=secret_key,
    symbol='SOL_USDC',
    base_spread_percentage=0.5,
    max_slippage_bps=50,  # 0.5%最大滑点
    enable_slippage_protection=True,

    # 永续合约参数
    target_position=1.0,
    max_position=5.0,
    inventory_skew=0.002,
)

strategy.run()
```

**Web模式**:
```json
POST /api/start
{
  "exchange": "backpack",
  "symbol": "SOL_USDC",
  "market_type": "perp",
  "spread": 0.5,
  "max_slippage_bps": 50
}
```

### 4.2 调整滑点阈值

**保守策略** (低风险):
```python
max_slippage_bps=30  # 0.3%
```

**激进策略** (高频交易):
```python
max_slippage_bps=100  # 1%
```

**禁用滑点保护** (不推荐):
```python
enable_slippage_protection=False
```

### 4.3 监控滑点情况

查看日志:
```bash
tail -f market_maker.log | grep -E "滑点|slippage"
```

示例输出:
```
[INFO] 滑点保护已启用: 最大滑点 50bp (0.50%)
[DEBUG] 价格偏离检查通过: 0.23% (参考: 145.320, 执行: 145.650, buy)
[ERROR] 价格偏离过大: 0.82% (限制: 0.50%) - 拒绝订单
```

### 4.4 运行时动态调整

```python
# 获取策略实例 (假设已运行)
strategy = current_strategy

# 调整滑点阈值
if strategy.slippage_protection:
    strategy.slippage_protection.set_max_slippage(80)  # 改为0.8%

# 临时禁用
strategy.slippage_protection.disable()

# 重新启用
strategy.slippage_protection.enable()
```

---

## 5. 完整示例

### 5.1 从零开始的安全配置

**步骤 1**: 克隆项目
```bash
git clone https://github.com/your-repo/Backpack-MM-Simple.git
cd Backpack-MM-Simple
```

**步骤 2**: 安装依赖
```bash
pip install -r requirements.txt
```

**步骤 3**: 创建 `.env` 文件
```bash
cp .env.example .env
nano .env  # 或使用你喜欢的编辑器
```

**步骤 4**: 配置环境变量
```bash
# .env 内容

# 主密码 (加密密钥库)
MASTER_PASSWORD=MyVeryStr0ngP@ssw0rd!2024

# Web认证
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Adm1nP@ss!Secure

# 临时明文密钥 (稍后迁移)
BACKPACK_KEY=your_backpack_key
BACKPACK_SECRET=your_backpack_secret
```

**步骤 5**: 迁移密钥到加密存储
```bash
python security/encryption.py migrate
```

**步骤 6**: 删除明文密钥
```bash
# 编辑 .env,删除 BACKPACK_KEY 和 BACKPACK_SECRET
nano .env
```

**步骤 7**: 启动Web服务
```bash
python run.py --mode web
```

**步骤 8**: 测试登录
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Adm1nP@ss!Secure"}'
```

**步骤 9**: 启动策略 (使用返回的token)
```bash
TOKEN="your-token-from-step-8"

curl -X POST http://localhost:5000/api/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exchange": "backpack",
    "symbol": "SOL_USDC",
    "spread": 0.5,
    "market_type": "perp",
    "target_position": 1.0,
    "max_position": 5.0,
    "inventory_skew": 0.002,
    "max_slippage_bps": 50,
    "stop_loss": 100,
    "take_profit": 200
  }'
```

### 5.2 生产环境检查清单

- [ ] 已设置强主密码 (`MASTER_PASSWORD`)
- [ ] 已迁移所有密钥到加密存储
- [ ] 已删除 `.env` 中的明文密钥
- [ ] `.keystore` 文件权限为 `0o600`
- [ ] 已设置强管理员密码 (`ADMIN_PASSWORD`)
- [ ] Web服务器使用HTTPS (反向代理)
- [ ] 防火墙仅允许必要端口
- [ ] 已配置滑点保护
- [ ] 已设置止损止盈
- [ ] 已启用日志记录
- [ ] 已设置监控告警
- [ ] 已测试紧急停止流程
- [ ] 已备份 `.keystore` 文件

---

## 6. 故障排除

### 6.1 密钥加密问题

**问题**: `ValueError: 必须提供主密码或设置MASTER_PASSWORD环境变量`

**解决**:
```bash
# 检查环境变量
echo $MASTER_PASSWORD

# 如果为空,设置它
export MASTER_PASSWORD="your-password"

# 或添加到 .env
echo 'MASTER_PASSWORD=your-password' >> .env
```

---

**问题**: `cryptography.fernet.InvalidToken`

**原因**: 主密码错误或 `.keystore` 文件损坏

**解决**:
```bash
# 检查是否使用了正确的主密码
# 如果确认密码正确但仍报错,可能需要重新迁移

# 1. 备份旧的keystore
mv .keystore .keystore.backup

# 2. 重新迁移
python security/encryption.py migrate
```

---

### 6.2 Web认证问题

**问题**: `401 Unauthorized` 即使提供了正确的token

**解决**:
```bash
# 检查token是否过期 (默认24小时)
# 重新登录获取新token

curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

---

**问题**: `429 Too Many Requests`

**原因**: 触发了速率限制

**解决**: 等待60秒后重试,或在代码中实现指数退避

---

### 6.3 滑点保护问题

**问题**: 订单被频繁拒绝 `slippage_protection_failed`

**解决方案 1**: 放宽滑点限制
```python
max_slippage_bps=100  # 从50bp增加到100bp
```

**解决方案 2**: 检查市场流动性
```python
# 查看日志中的偏离详情
# 如果市场波动剧烈,考虑暂停策略
```

**解决方案 3**: 临时禁用 (仅测试)
```python
enable_slippage_protection=False
```

---

**问题**: `market_order_protection_failed: 价差过大`

**原因**: 买卖价差超过100bp

**解决**:
1. 检查市场是否正常
2. 考虑使用限价单而非市价单
3. 调整价差阈值 (需修改代码)

---

### 6.4 日志和调试

**启用详细日志**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**查看实时日志**:
```bash
tail -f market_maker.log
```

**过滤特定模块**:
```bash
tail -f market_maker.log | grep "security.auth"
tail -f market_maker.log | grep "perp_market_maker"
```

---

## 7. 安全最佳实践

### 7.1 密码管理

✅ **推荐**:
- 使用密码管理器生成强密码
- 主密码至少16个字符
- 定期更换密码 (每3-6个月)
- 不要在代码中硬编码密码

❌ **避免**:
- 使用简单密码 (如 "password123")
- 在多个系统使用相同密码
- 将密码写在纸上或未加密的文件中

### 7.2 密钥备份

**备份 `.keystore` 文件**:
```bash
# 加密备份
gpg -c .keystore  # 输入备份密码
# 生成 .keystore.gpg

# 上传到安全位置 (如加密云存储)
# 或存储到离线USB设备
```

**恢复**:
```bash
gpg .keystore.gpg  # 输入备份密码
# 恢复 .keystore
```

### 7.3 生产环境部署

**使用HTTPS**:
```bash
# 使用Nginx反向代理
# /etc/nginx/sites-available/mm-bot

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**防火墙配置**:
```bash
# 仅允许SSH和HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

**运行在隔离环境**:
```bash
# 使用Docker
docker run -d \
  --name mm-bot \
  -e MASTER_PASSWORD=$MASTER_PASSWORD \
  -e ADMIN_PASSWORD=$ADMIN_PASSWORD \
  -v $(pwd)/.keystore:/app/.keystore:ro \
  -p 5000:5000 \
  mm-bot:latest
```

---

## 8. 支持和反馈

如遇到问题:
1. 查看 `SECURITY_ANALYSIS.md` 中的详细说明
2. 检查 GitHub Issues
3. 提交新的Issue (包含日志和复现步骤)

---

**文档版本**: 1.0
**最后更新**: 2025-11-14
