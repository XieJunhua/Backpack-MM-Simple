# 儀表盤配置說明

## 🎯 最新更新

### 1. 優化佈局

整體績效指標已移到頂部，方便快速查看歷史累計數據：

```
實時狀態
  ↓
整體績效指標（歷史累計）← 新位置！
  ↓
實時統計卡片（本次運行）
  ↓
圖表 + 交易記錄
```

### 2. 禁用控制面板選項

如果你只需要數據展示功能，不需要啟動/停止機器人的控制功能，可以啟用此選項。

---

## 📋 配置方法

### 方法 1: 環境變量

在服務器上設置環境變量：

```bash
# Linux/macOS
export DISABLE_CONTROL_PANEL=true

# 啟動 Web 服務器
python web/server.py
```

### 方法 2: .env 文件

在 `.env` 文件中添加：

```bash
# 禁用控制面板，只保留數據儀表盤
DISABLE_CONTROL_PANEL=true
```

然後啟動服務器：

```bash
python web/server.py
```

### 方法 3: 臨時設置（單次使用）

```bash
# 一次性設置並啟動
DISABLE_CONTROL_PANEL=true python web/server.py
```

---

## 🔍 效果對比

### 啟用前 (DISABLE_CONTROL_PANEL=false 或未設置)

- 訪問 `/` → 顯示控制面板（可啟動/停止機器人）
- 訪問 `/dashboard` → 顯示數據儀表盤
- 導航欄顯示：`[控制面板] [刷新數據]`

### 啟用後 (DISABLE_CONTROL_PANEL=true)

- 訪問 `/` → **自動重定向**到 `/dashboard`
- 訪問 `/dashboard` → 顯示數據儀表盤
- 導航欄顯示：`[刷新數據]` ← 控制面板鏈接已隱藏

---

## 💡 使用場景

### 推薦啟用此選項的情況：

1. **僅展示數據** - 機器人在服務器後台運行，只需要查看數據
2. **公開展示** - 向他人展示交易數據，但不希望暴露控制功能
3. **簡化界面** - 減少不必要的功能，專注於數據分析
4. **多用戶環境** - 限制普通用戶的操作權限

### 不推薦啟用的情況：

1. 需要通過 Web 界面啟動/停止機器人
2. 需要調整策略參數
3. 只有一個管理員使用系統

---

## 🚀 完整啟動示例

### 場景 1: 僅數據展示（推薦生產環境）

```bash
# 1. 設置環境變量
export DISABLE_CONTROL_PANEL=true
export WEB_HOST=0.0.0.0  # 允許外部訪問
export WEB_PORT=5000

# 2. 後台運行機器人（使用 screen 或 tmux）
screen -S trading-bot
python run.py --exchange backpack --symbol SOL_USDC_PERP --enable-db ...

# 3. 在另一個終端啟動 Web 服務器
screen -S web-server
python web/server.py

# 現在訪問 http://your-server-ip:5000 會自動顯示儀表盤
```

### 場景 2: 完整控制（開發/測試環境）

```bash
# 不設置 DISABLE_CONTROL_PANEL 或設為 false
export DISABLE_CONTROL_PANEL=false

# 啟動 Web 服務器
python web/server.py

# 訪問 http://localhost:5000/ 可以啟動/停止機器人
# 訪問 http://localhost:5000/dashboard 查看數據
```

---

## ⚙️ 技術細節

### 實現方式

1. **重定向機制**
   ```python
   # web/server.py
   @app.route('/')
   def index():
       disable_control = os.getenv('DISABLE_CONTROL_PANEL', 'false').lower() in ('true', '1', 'yes')
       if disable_control:
           return redirect('/dashboard')
       return render_template('index.html')
   ```

2. **模板條件渲染**
   ```html
   <!-- web/templates/dashboard.html -->
   {% if not disable_control %}
   <a href="/" class="btn btn-outline-light btn-sm me-2">
       <i class="bi bi-gear"></i> 控制面板
   </a>
   {% endif %}
   ```

### 支持的環境變量值

以下值會被識別為 `true`（啟用禁用控制面板）：
- `true`
- `True`
- `TRUE`
- `1`
- `yes`
- `Yes`
- `YES`

其他任何值都會被視為 `false`（保留控制面板）。

---

## 📊 新增指標

整體績效指標區域新增了以下統計：

| 指標 | 說明 | 格式 |
|------|------|------|
| **買入交易** | 買入方向的交易數量和佔比 | `數量 (百分比)` |
| **賣出交易** | 賣出方向的交易數量和佔比 | `數量 (百分比)` |

示例顯示：
```
買入交易: 250 (51.0%)
賣出交易: 240 (49.0%)
```

---

## 🔒 安全提示

即使禁用了控制面板，以下 API 端點仍然**需要認證**才能訪問：

- `/api/start` - 啟動機器人
- `/api/stop` - 停止機器人
- `/api/logout` - 登出

儀表盤的所有只讀 API 端點（`/api/dashboard/*`）**不需要認證**。

如果你需要完全保護數據：

```bash
# 方法1: 使用防火牆限制訪問
sudo ufw allow from 你的IP地址 to any port 5000

# 方法2: 使用 Nginx 反向代理 + 基本認證
# 方法3: 使用 VPN 訪問
```

---

## 🐛 故障排除

### 問題1: 設置了 DISABLE_CONTROL_PANEL=true 但仍能看到控制面板

**檢查**:
```bash
# 確認環境變量已設置
echo $DISABLE_CONTROL_PANEL

# 應該輸出: true
```

**解決方案**:
```bash
# 重啟 Web 服務器
pkill -f "python web/server.py"
DISABLE_CONTROL_PANEL=true python web/server.py
```

### 問題2: 訪問 / 沒有重定向

**檢查瀏覽器緩存**:
- 清除瀏覽器緩存
- 使用無痕模式訪問
- 強制刷新（Ctrl+F5）

### 問題3: 想臨時訪問控制面板

**方法1: 臨時禁用**
```bash
# 設置為 false 並重啟
export DISABLE_CONTROL_PANEL=false
python web/server.py
```

**方法2: 直接修改 .env**
```bash
# 編輯 .env 文件
DISABLE_CONTROL_PANEL=false

# 重啟服務器
```

---

## 📝 總結

```bash
# 快速配置命令

# 僅儀表盤模式（推薦生產環境）
echo "DISABLE_CONTROL_PANEL=true" >> .env

# 完整功能模式（開發/測試）
echo "DISABLE_CONTROL_PANEL=false" >> .env
```

更多信息請查看：
- [儀表盤使用說明](DASHBOARD_USAGE.md)
- [安全設置文檔](SECURITY_SETUP.md)

---

**版本**: 1.0
**最後更新**: 2025-11-14
