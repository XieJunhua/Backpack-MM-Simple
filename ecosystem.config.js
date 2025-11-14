module.exports = {
  apps: [
    {
      name: "sol_perp_mm",
      script: "run.py",
      interpreter: "python3",
      cwd: "/root/github/Backpack-MM-Simple",  // 修改为你的项目路径
      args: [
        "--exchange", "backpack",
        "--market-type", "perp",
        "--symbol", "SOL_USDC_PERP",
        "--strategy", "standard",
        "--spread", "0.007",              // 0.7% 价差
        "--quantity", "0.1",              // 0.1 SOL 每单
        "--max-orders", "2",              // 2对订单
        "--target-position", "0",         // 目标中性持仓
        "--max-position", "1.5",          // 最大持仓 1.5 SOL
        "--position-threshold", "0.8",    // 持仓偏离 0.8 触发调整
        "--inventory-skew", "0.6",        // 库存偏移 60%（启用调整）
        "--stop-loss", "50",              // 止损 -50 USDC
        "--take-profit", "100",           // 止盈 +100 USDC
        "--duration", "86400",            // 运行 24 小时
        "--interval", "30",               // 30 秒调整一次
        "--enable-db"                     // 启用数据库记录
      ],

      // 环境变量
      env: {
        MASTER_PASSWORD: process.env.MASTER_PASSWORD || "",
        ADMIN_PASSWORD: process.env.ADMIN_PASSWORD || "",
        DISABLE_CONTROL_PANEL: "true",
        WEB_HOST: "0.0.0.0",
        WEB_PORT: "5000",
        PYTHONUNBUFFERED: "1"  // 立即输出日志，不缓冲
      },

      // 进程管理
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_restarts: 20,              // 增加最大重启次数
      min_uptime: "10s",             // 最小运行时间
      restart_delay: 5000,           // 重启延迟 5 秒
      exp_backoff_restart_delay: 100, // 指数退避重启

      // 日志管理
      error_file: "./logs/sol_perp_mm_err.log",
      out_file: "./logs/sol_perp_mm_out.log",
      log_file: "./logs/sol_perp_mm_combined.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,

      // 自动重启时间（每天凌晨4点重启）
      cron_restart: "0 4 * * *",

      // 监控
      time: true,

      // 错误处理
      kill_timeout: 5000,
      listen_timeout: 3000,
      shutdown_with_message: false
    }
  ]
};
