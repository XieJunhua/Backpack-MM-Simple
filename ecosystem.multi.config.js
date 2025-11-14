/**
 * PM2 配置文件 - 多策略版本
 *
 * 使用方法:
 *   启动平衡配置: pm2 start ecosystem.multi.config.js --only sol_perp_balanced
 *   启动保守配置: pm2 start ecosystem.multi.config.js --only sol_perp_conservative
 *   启动全部:      pm2 start ecosystem.multi.config.js
 *
 * 查看状态: pm2 status
 * 查看日志: pm2 logs sol_perp_balanced
 * 停止:    pm2 stop sol_perp_balanced
 * 重启:    pm2 restart sol_perp_balanced
 */

module.exports = {
  apps: [
    // ============================================================
    // 配置1: 平衡配置（推荐）
    // 特点: 中等成交量，合理风控，稳定收益
    // ============================================================
    {
      name: "sol_perp_balanced",
      script: "run.py",
      interpreter: "python3",
      cwd: "/root/github/Backpack-MM-Simple",  // 修改为你的实际路径
      args: [
        "--exchange", "backpack",
        "--market-type", "perp",
        "--symbol", "SOL_USDC_PERP",
        "--strategy", "standard",
        "--spread", "0.007",              // 0.7% 价差
        "--quantity", "0.08",             // 0.08 SOL
        "--max-orders", "2",
        "--target-position", "0",
        "--max-position", "1.5",          // 限制持仓 1.5 SOL
        "--position-threshold", "0.8",
        "--inventory-skew", "0.6",        // 启用调整
        "--stop-loss", "50",              // -50 USDC 止损
        "--take-profit", "100",           // +100 USDC 止盈
        "--duration", "86400",            // 24 小时
        "--interval", "30",
        "--enable-db"
      ],
      env: {
        MASTER_PASSWORD: process.env.MASTER_PASSWORD || "",
        ADMIN_PASSWORD: process.env.ADMIN_PASSWORD || "",
        DISABLE_CONTROL_PANEL: "true",
        PYTHONUNBUFFERED: "1"
      },
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_restarts: 20,
      min_uptime: "10s",
      restart_delay: 5000,
      exp_backoff_restart_delay: 100,
      error_file: "./logs/balanced_err.log",
      out_file: "./logs/balanced_out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
      cron_restart: "0 4 * * *",  // 每天凌晨4点重启
      time: true
    },

    // ============================================================
    // 配置2: 保守配置
    // 特点: 低风险，小持仓，稳定收益
    // ============================================================
    {
      name: "sol_perp_conservative",
      script: "run.py",
      interpreter: "python3",
      cwd: "/root/github/Backpack-MM-Simple",
      args: [
        "--exchange", "backpack",
        "--market-type", "perp",
        "--symbol", "SOL_USDC_PERP",
        "--strategy", "standard",
        "--spread", "0.005",              // 0.5% 价差（高频成交）
        "--quantity", "0.05",             // 0.05 SOL
        "--max-orders", "1",
        "--target-position", "0",
        "--max-position", "0.5",          // 严格限制 0.5 SOL
        "--position-threshold", "0.2",
        "--inventory-skew", "0.9",        // 强力引导归零
        "--stop-loss", "20",              // -20 USDC 止损
        "--take-profit", "50",            // +50 USDC 止盈
        "--duration", "86400",
        "--interval", "30",
        "--enable-db"
      ],
      env: {
        MASTER_PASSWORD: process.env.MASTER_PASSWORD || "",
        ADMIN_PASSWORD: process.env.ADMIN_PASSWORD || "",
        DISABLE_CONTROL_PANEL: "true",
        PYTHONUNBUFFERED: "1"
      },
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_restarts: 20,
      min_uptime: "10s",
      restart_delay: 5000,
      exp_backoff_restart_delay: 100,
      error_file: "./logs/conservative_err.log",
      out_file: "./logs/conservative_out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
      cron_restart: "0 4 * * *",
      time: true
    },

    // ============================================================
    // 配置3: 激进配置（高风险高收益）
    // 特点: 大持仓，追求高收益，风险较高
    // 注意: 需要密切监控
    // ============================================================
    {
      name: "sol_perp_aggressive",
      script: "run.py",
      interpreter: "python3",
      cwd: "/root/github/Backpack-MM-Simple",
      args: [
        "--exchange", "backpack",
        "--market-type", "perp",
        "--symbol", "SOL_USDC_PERP",
        "--strategy", "standard",
        "--spread", "0.01",               // 1% 价差（较大）
        "--quantity", "0.15",             // 0.15 SOL
        "--max-orders", "3",
        "--target-position", "0",
        "--max-position", "3.0",          // 允许 3 SOL 持仓
        "--position-threshold", "1.5",
        "--inventory-skew", "0.4",        // 温和调整
        "--stop-loss", "100",             // -100 USDC 止损
        "--take-profit", "200",           // +200 USDC 止盈
        "--duration", "86400",
        "--interval", "60",               // 60秒调整
        "--enable-db"
      ],
      env: {
        MASTER_PASSWORD: process.env.MASTER_PASSWORD || "",
        ADMIN_PASSWORD: process.env.ADMIN_PASSWORD || "",
        DISABLE_CONTROL_PANEL: "true",
        PYTHONUNBUFFERED: "1"
      },
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_restarts: 20,
      min_uptime: "10s",
      restart_delay: 5000,
      exp_backoff_restart_delay: 100,
      error_file: "./logs/aggressive_err.log",
      out_file: "./logs/aggressive_out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
      cron_restart: "0 4 * * *",
      time: true
    },

    // ============================================================
    // 配置4: Web 数据仪表盘（可选）
    // 用途: 提供 http://IP:5000/dashboard 访问数据
    // ============================================================
    {
      name: "web_dashboard",
      script: "web/server.py",
      interpreter: "python3",
      cwd: "/root/github/Backpack-MM-Simple",
      args: [],
      env: {
        MASTER_PASSWORD: process.env.MASTER_PASSWORD || "",
        ADMIN_PASSWORD: process.env.ADMIN_PASSWORD || "",
        DISABLE_CONTROL_PANEL: "true",    // 只保留仪表盘
        WEB_HOST: "0.0.0.0",              // 允许外部访问
        WEB_PORT: "5000",
        WEB_DEBUG: "false",
        PYTHONUNBUFFERED: "1"
      },
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: "5s",
      restart_delay: 3000,
      error_file: "./logs/web_err.log",
      out_file: "./logs/web_out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
      time: true
    }
  ]
};
