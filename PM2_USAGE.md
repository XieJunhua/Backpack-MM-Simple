# PM2 使用指南

## 📋 概述

本项目提供了 PM2 配置文件：

**ecosystem.config.js** - 平衡配置（推荐使用）

---

## 🚀 快速开始

### 1. 安装 PM2

```bash
# 全局安装 PM2
npm install -g pm2

# 验证安装
pm2 --version
```

### 2. 设置环境变量

```bash
# 方法1: 临时设置（当前终端有效）
export MASTER_PASSWORD="your-master-password"
export ADMIN_PASSWORD="your-admin-password"

# 方法2: 永久设置（推荐）
# 编辑 ~/.bashrc 或 ~/.bash_profile
echo 'export MASTER_PASSWORD="your-master-password"' >> ~/.bashrc
echo 'export ADMIN_PASSWORD="your-admin-password"' >> ~/.bashrc
source ~/.bashrc

# 验证
echo $MASTER_PASSWORD
```

### 3. 修改配置文件路径

编辑 `ecosystem.config.js`：

```javascript
cwd: "/root/github/Backpack-MM-Simple",  // 改为你的实际项目路径
```

---

## 📁 启动和管理

### 启动策略

```bash
cd /root/github/Backpack-MM-Simple

# 启动做市策略
pm2 start ecosystem.config.js

# 查看状态
pm2 status
pm2 logs sol_perp_mm

# 实时监控
pm2 monit
```

### 常用命令

```bash
# 查看状态
pm2 status
pm2 list

# 查看日志
pm2 logs sol_perp_mm           # 实时日志
pm2 logs sol_perp_mm --lines 100  # 最近100行
pm2 logs sol_perp_mm --err     # 只看错误日志

# 停止/重启
pm2 stop sol_perp_mm
pm2 restart sol_perp_mm
pm2 reload sol_perp_mm         # 零停机重启

# 删除
pm2 delete sol_perp_mm

# 保存配置（开机自启）
pm2 save
pm2 startup  # 生成开机启动脚本
```

---

## 📊 配置说明

| 配置 | 价差 | 单量 | 持仓限制 | 风险 | 适合人群 |
|-----|------|------|---------|------|---------|
| **平衡** | 0.7% | 0.1 SOL | 1.5 SOL | ⚠️ 中 | 大部分用户 |

---

## 🔍 监控和日志

### 实时监控

```bash
# 终端监控界面
pm2 monit

# Web 监控（需要安装 pm2-web）
pm2 web
# 访问 http://localhost:9615
```

### 查看日志

```bash
# 实时日志（所有进程）
pm2 logs

# 指定进程日志
pm2 logs sol_perp_mm

# 查看错误日志
pm2 logs sol_perp_mm --err

# 清空日志
pm2 flush

# 日志文件位置
ls -lh logs/
```

### 查看详细信息

```bash
# 进程详情
pm2 show sol_perp_mm

# 内存使用
pm2 describe sol_perp_mm

# 环境变量
pm2 env 0  # 0 是进程 ID
```

---

## ⚙️ 高级配置

### 自动重启时间

配置文件中已设置每天凌晨 4 点自动重启：

```javascript
cron_restart: "0 4 * * *"
```

修改重启时间：
```javascript
cron_restart: "0 2 * * *"   // 凌晨2点
cron_restart: "0 */6 * * *" // 每6小时
cron_restart: "0 0 * * 0"   // 每周日凌晨
```

### 资源限制

```javascript
max_memory_restart: "500M",  // 内存超过 500MB 重启
max_restarts: 20,            // 最多重启 20 次
min_uptime: "10s"            // 最小运行 10 秒才算成功
```

### 日志轮转

安装 PM2 日志轮转模块：

```bash
pm2 install pm2-logrotate

# 配置日志轮转
pm2 set pm2-logrotate:max_size 10M        # 日志大小限制
pm2 set pm2-logrotate:retain 7            # 保留 7 天
pm2 set pm2-logrotate:compress true       # 压缩旧日志
pm2 set pm2-logrotate:rotateInterval '0 0 * * *'  # 每天轮转
```

---

## 🛠️ 故障排除

### 问题1: 进程启动后立即退出

```bash
# 查看详细日志
pm2 logs sol_perp_mm --lines 200

# 常见原因:
# 1. MASTER_PASSWORD 未设置
# 2. 项目路径错误
# 3. Python 依赖缺失
# 4. API 密钥未配置
```

**解决方案**:
```bash
# 检查环境变量
echo $MASTER_PASSWORD

# 检查项目路径
ls /root/github/Backpack-MM-Simple/run.py

# 检查 Python 依赖
pip list | grep cryptography

# 测试手动运行
cd /root/github/Backpack-MM-Simple
python3 run.py --exchange backpack --market-type perp --symbol SOL_USDC_PERP --spread 0.007 --quantity 0.1
```

---

### 问题2: 频繁重启

```bash
# 查看重启次数
pm2 status

# 如果重启次数很多，检查:
pm2 logs sol_perp_mm --err --lines 100
```

**常见原因**:
- 止损频繁触发（调整 `--stop-loss`）
- API 密钥错误
- 网络连接问题
- 资金不足

---

### 问题3: 日志文件过大

```bash
# 查看日志大小
ls -lh logs/

# 清空日志
pm2 flush

# 安装日志轮转（见上方）
pm2 install pm2-logrotate
```

---

### 问题4: 环境变量不生效

```bash
# PM2 读取的是启动时的环境变量
# 修改后需要重启 PM2

# 删除所有进程
pm2 delete all

# 重新加载环境变量
source ~/.bashrc

# 重新启动
pm2 start ecosystem.config.js
```

---

## 📱 远程监控（可选）

### PM2 Plus（官方云监控）

```bash
# 注册 PM2 Plus 账号
# https://app.pm2.io/

# 连接到 PM2 Plus
pm2 link <secret_key> <public_key>

# 现在可以在网页上监控进程
# 包括 CPU、内存、错误提醒等
```

### Telegram 告警（自定义）

可以配合 `pm2-telegram` 模块实现 Telegram 告警：

```bash
npm install -g pm2-telegram

pm2 install pm2-telegram
pm2 set pm2-telegram:token <telegram_bot_token>
pm2 set pm2-telegram:chat_id <your_chat_id>
```

---

## 🔄 更新策略

### 修改参数后重启

```bash
# 编辑配置文件
vim ecosystem.config.js

# 重启生效
pm2 restart sol_perp_mm

# 或者删除后重新启动
pm2 delete sol_perp_mm
pm2 start ecosystem.config.js
```

### 更新代码后重启

```bash
cd /root/github/Backpack-MM-Simple

# 拉取最新代码
git pull

# 重启所有进程
pm2 restart all

# 或者只重启策略
pm2 restart sol_perp_mm
```

---

## 💾 备份和恢复

### 保存当前进程列表

```bash
# 保存当前所有进程配置
pm2 save

# 配置文件位置: ~/.pm2/dump.pm2
```

### 开机自启动

```bash
# 生成启动脚本（只需执行一次）
pm2 startup

# 按提示执行输出的命令，例如:
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u root --hp /root

# 保存当前进程列表
pm2 save

# 现在系统重启后会自动启动所有进程
```

### 禁用自启动

```bash
pm2 unstartup
```

---

## 📝 最佳实践

### 1. 先测试再部署

```bash
# 手动运行测试
python3 run.py --exchange backpack --market-type perp --symbol SOL_USDC_PERP --spread 0.007 --quantity 0.1 --duration 600

# 确认无误后用 PM2 启动
pm2 start ecosystem.config.js
```

### 2. 定期检查日志

```bash
# 每天检查一次
pm2 logs sol_perp_mm --lines 100 --nostream

# 查看错误
pm2 logs sol_perp_mm --err --lines 50
```

### 3. 监控资源使用

```bash
# 实时监控
pm2 monit

# 检查内存
pm2 describe sol_perp_mm | grep memory
```

### 4. 定期备份数据库

```bash
# 备份交易数据
cp trading_data.db backup/trading_data_$(date +%Y%m%d).db
```

---

## 📞 常用命令速查

```bash
# 启动
pm2 start ecosystem.config.js

# 查看状态
pm2 status
pm2 list

# 查看日志
pm2 logs
pm2 logs sol_perp_mm

# 监控
pm2 monit

# 重启
pm2 restart sol_perp_mm
pm2 reload sol_perp_mm

# 停止
pm2 stop sol_perp_mm

# 删除
pm2 delete sol_perp_mm
pm2 delete all

# 保存/恢复
pm2 save
pm2 resurrect

# 清空日志
pm2 flush

# 更新 PM2
npm install -g pm2@latest
pm2 update
```

---

**版本**: 1.0
**最后更新**: 2025-11-14
**作者**: Claude Code
