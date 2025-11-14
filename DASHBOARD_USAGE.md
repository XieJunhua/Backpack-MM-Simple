# 量化數據儀表盤使用說明

## 📊 概述

新增的量化數據儀表盤是一個**只讀**的數據展示頁面，用於可視化展示交易機器人的量化數據和績效指標。

---

## 🚀 快速開始

### 1. 啟動 Web 服務器

```bash
# 方法1: 直接運行
python web/server.py

# 方法2: 指定端口
WEB_PORT=5000 python web/server.py
```

### 2. 訪問頁面

- **控制面板**: http://localhost:5000/ （原有功能，啟動/停止機器人）
- **數據儀表盤**: http://localhost:5000/dashboard （新增，只讀數據展示）

---

## 🎯 儀表盤功能

### 實時統計概覽

顯示當前運行狀態和關鍵指標：

| 指標 | 說明 |
|------|------|
| **總餘額 (USDC)** | 當前賬戶總餘額（包含普通餘額和抵押品餘額） |
| **累計盈虧 (USDC)** | 扣除手續費後的淨盈虧 |
| **成交額 (USDC)** | 本次運行的總成交金額 |
| **成交筆數** | 本次運行的總交易數量（買/賣分別顯示） |

### 詳細指標

| 指標 | 說明 |
|------|------|
| **磨損率** | 累計盈虧 / 成交額 × 100%，衡量交易效率 |
| **手續費 (USDC)** | 本次運行的總手續費支出 |
| **當前價格** | 交易對的實時市場價格 |
| **運行時間** | 本次會話的運行時長 |

### 圖表展示

1. **每日盈虧趨勢** (最近7天)
   - 柱狀圖展示每日淨利潤
   - 綠色表示盈利，紅色表示虧損

2. **每日成交量趨勢** (最近7天)
   - 折線圖展示 Maker 和 Taker 成交量
   - 藍色線: Maker 成交量
   - 紫色線: Taker 成交量

### 交易記錄表格

展示最近100筆交易的詳細信息：

- 時間
- 方向（買入/賣出）
- 類型（Maker/Taker）
- 數量
- 價格
- 成交額
- 手續費

### 整體績效指標

匯總統計所有歷史交易數據：

- 總交易筆數
- Maker 交易比例
- 平均成交價
- 平均成交量
- 總成交額
- 總手續費
- 淨利潤
- Maker 成交量

---

## 🔄 數據更新機制

### 自動更新

- **實時數據**: 每 **5秒** 自動刷新一次（總餘額、盈虧、成交量等）
- **歷史數據**: 需要手動點擊「刷新數據」按鈕

### 手動刷新

點擊右上角的 **「刷新數據」** 按鈕，會同時更新：
- 當前運行狀態
- 歷史統計圖表
- 交易記錄表格
- 績效指標

---

## 📡 API 端點

儀表盤使用以下只讀 API 端點獲取數據：

### 1. 獲取當前狀態

```
GET /api/dashboard/current
```

**響應示例**:
```json
{
  "bot_status": {
    "running": true,
    "start_time": "2025-11-14T10:00:00"
  },
  "stats": {
    "quote_balance": 1000.50,
    "cumulative_pnl": 12.34,
    "total_volume_usdc": 5000.00,
    "total_trades": 50
  }
}
```

### 2. 獲取歷史統計

```
GET /api/dashboard/history?symbol=SOL_USDC_PERP&days=7
```

**參數**:
- `symbol`: 交易對符號（默認: SOL_USDC）
- `days`: 天數（默認: 7）

**響應示例**:
```json
{
  "success": true,
  "symbol": "SOL_USDC_PERP",
  "daily_stats": [
    {
      "date": "2025-11-14",
      "maker_buy_volume": 100.5,
      "maker_sell_volume": 98.3,
      "net_profit": 5.67,
      "total_fees": 1.23
    }
  ],
  "all_time_stats": {
    "total_profit": 50.00,
    "total_fees": 10.00
  }
}
```

### 3. 獲取交易記錄

```
GET /api/dashboard/trades?symbol=SOL_USDC_PERP&limit=100
```

**參數**:
- `symbol`: 交易對符號（默認: SOL_USDC）
- `limit`: 返回記錄數量（默認: 100）

**響應示例**:
```json
{
  "success": true,
  "symbol": "SOL_USDC_PERP",
  "trades": [
    {
      "side": "Bid",
      "quantity": 1.5,
      "price": 100.50,
      "maker": true,
      "fee": 0.15,
      "timestamp": "2025-11-14T10:30:00"
    }
  ]
}
```

### 4. 獲取績效指標

```
GET /api/dashboard/performance?symbol=SOL_USDC_PERP
```

**響應示例**:
```json
{
  "success": true,
  "symbol": "SOL_USDC_PERP",
  "performance": {
    "total_trades": 500,
    "maker_trades": 450,
    "avg_price": 100.25,
    "total_volume": 50000.00,
    "total_net_profit": 123.45
  }
}
```

---

## 🎨 界面特性

### 暗色主題

- 專為長時間使用設計的暗色主題
- 降低眼睛疲勞
- 類似 GitHub 的現代化設計

### 顏色編碼

| 顏色 | 含義 |
|------|------|
| 🟢 綠色 | 正數（盈利） |
| 🔴 紅色 | 負數（虧損） |
| 🔵 藍色 | 中性數據 |

### 徽章標識

- **運行中**: 綠色徽章
- **停止**: 灰色徽章
- **買入**: 綠色標籤
- **賣出**: 紅色標籤
- **Maker**: 藍色標籤
- **Taker**: 紫色標籤

### 響應式設計

- 支持桌面、平板、手機等不同螢幕尺寸
- 自適應佈局，在小螢幕上自動調整

---

## 🔒 安全性

### 只讀訪問

- **不需要認證**: 儀表盤是只讀的，可以直接訪問
- **無操作權限**: 無法啟動/停止機器人
- **數據安全**: 所有數據從數據庫讀取，不涉及 API 密鑰

### 控制面板

如果需要**啟動/停止**機器人，請訪問 `/`（控制面板），該頁面需要認證。

---

## 📊 數據來源

所有數據來自項目的 SQLite 數據庫 (`database/db.py`)：

### 數據表

1. **completed_orders**: 完成的訂單記錄
2. **trading_stats**: 每日交易統計
3. **market_data**: 市場數據
4. **rebalance_orders**: 重平衡訂單

### 啟用數據庫

確保在運行策略時啟用數據庫記錄：

```bash
python run.py --exchange backpack \
  --symbol SOL_USDC_PERP \
  --enable-db  # ← 啟用數據庫記錄
```

或在 Web 控制面板中勾選「啟用數據庫」選項。

---

## 🛠️ 故障排除

### 問題1: 儀表盤顯示「數據庫模塊未啟用」

**原因**: 數據庫模塊導入失敗

**解決方案**:
1. 確保 `database/db.py` 存在
2. 確保 SQLite3 已安裝
3. 檢查數據庫文件權限

### 問題2: 圖表顯示為空

**原因**: 數據庫中沒有歷史數據

**解決方案**:
1. 確保運行策略時啟用了 `--enable-db`
2. 至少運行一段時間讓數據積累
3. 檢查數據庫文件是否存在: `ls -la *.db`

### 問題3: 實時數據不更新

**原因**: 機器人未運行或 WebSocket 連接失敗

**解決方案**:
1. 檢查機器人是否在運行（查看狀態徽章）
2. 手動點擊「刷新數據」按鈕
3. 刷新瀏覽器頁面

### 問題4: 交易記錄為空

**原因**:
- 數據庫記錄未啟用
- 尚未產生交易

**解決方案**:
1. 確保 `--enable-db` 已啟用
2. 等待策略產生交易
3. 檢查數據庫中是否有記錄:
   ```bash
   sqlite3 trading_data.db "SELECT COUNT(*) FROM completed_orders;"
   ```

---

## 💡 使用建議

### 1. 多交易對監控

如果運行多個交易對，可以在 URL 中指定 symbol 參數：

```
http://localhost:5000/dashboard?symbol=BTC_USDC_PERP
```

（需要修改前端代碼以支持該功能）

### 2. 定期導出數據

建議定期備份數據庫文件：

```bash
cp trading_data.db "backup/trading_data_$(date +%Y%m%d).db"
```

### 3. 性能優化

如果數據量很大（>10萬筆交易），建議：
- 限制查詢的時間範圍
- 定期清理舊數據
- 為數據庫添加索引

### 4. 遠程訪問

如果需要從其他設備訪問儀表盤：

```bash
# 監聽所有網絡接口
WEB_HOST=0.0.0.0 python web/server.py
```

然後訪問: `http://<服務器IP>:5000/dashboard`

⚠️ **安全提示**: 如果開放到公網，建議配置防火牆或使用 VPN。

---

## 📝 自定義開發

### 添加新指標

1. 在 `web/server.py` 中添加新的 API 端點
2. 在 `dashboard.html` 中添加對應的顯示元素
3. 使用 JavaScript 調用 API 並更新界面

### 修改圖表

圖表使用 [Chart.js 3](https://www.chartjs.org/)，可以輕鬆自定義：

```javascript
// 修改圖表類型
pnlChart = new Chart(ctx, {
    type: 'line',  // 改為折線圖
    // ...
});

// 添加新的數據集
pnlChart.data.datasets.push({
    label: '新指標',
    data: [...],
    backgroundColor: '#ff0000'
});
```

### 自定義主題

在 `dashboard.html` 的 `<style>` 標籤中修改顏色：

```css
body {
    background-color: #你的顏色;
    color: #你的顏色;
}
```

---

## 🔗 相關文檔

- [Web 服務器文檔](web/server.py)
- [數據庫文檔](database/db.py)
- [安全設置文檔](SECURITY_SETUP.md)
- [Chart.js 官方文檔](https://www.chartjs.org/docs/latest/)
- [Bootstrap 5 官方文檔](https://getbootstrap.com/docs/5.1/getting-started/introduction/)

---

## 📞 支持

如果遇到問題或有功能建議，請：

1. 查看故障排除章節
2. 檢查日誌文件: `logs/web_server.log`
3. 提交 Issue 到 GitHub 倉庫

---

**版本**: 1.0
**最後更新**: 2025-11-14
**作者**: Claude Code

---

## 🎉 功能亮點

✅ **完全只讀** - 無需認證，安全便捷
✅ **實時更新** - 每5秒自動刷新最新數據
✅ **豐富圖表** - 直觀展示盈虧和成交量趨勢
✅ **詳細記錄** - 最近100筆交易一目了然
✅ **響應式設計** - 支持各種設備訪問
✅ **暗色主題** - 長時間使用不累眼
✅ **性能優化** - 快速加載，流暢體驗
