module.exports = {
  apps: [
    {
      name: "sol_perp_mm",
      script: "run.py",
      interpreter: "python3",
      cwd: "/root/github/Backpack-MM-Simple", // 修改为你的项目路径
      args: [
        "--exchange",
        "backpack",
        "--market-type",
        "perp",
        "--symbol",
        "SOL_USDC_PERP",
        "--strategy",
        "standard",
        "--spread",
        "0.06", // 0.06% 价差（覆盖手续费）
        "--quantity",
        "0.5", // 0.5 SOL 每单
        "--max-orders",
        "2", // 2对订单
        "--target-position",
        "0", // 目标中性持仓
        "--max-position",
        "1.5", // 最大持仓 1.5 SOL
        "--position-threshold",
        "0.8", // 持仓偏离 0.8 触发调整
        "--inventory-skew",
        "0.6", // 库存偏移 60%（启用调整）
        "--stop-loss",
        "10", // 止损 -10 USDC
        "--take-profit",
        "10", // 止盈 +10 USDC
        "--duration",
        "86400", // 运行 24 小时
        "--interval",
        "10", // 30 秒调整一次
        "--enable-db", // 启用数据库记录
      ],

      // 环境变量
      env: {
        DISABLE_CONTROL_PANEL: "true",
        WEB_HOST: "0.0.0.0",
        WEB_PORT: "5000",
        PYTHONUNBUFFERED: "1", // 立即输出日志，不缓冲
      },

      // 进程管理
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_restarts: 20, // 增加最大重启次数
      min_uptime: "10s", // 最小运行时间
      restart_delay: 5000, // 重启延迟 5 秒
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
      shutdown_with_message: false,
    },

    // Aster 交易所配置
    {
      name: "aster_sol_perp",
      script: "run.py",
      interpreter: "python3",
      cwd: "/root/github/Backpack-MM-Simple", // 修改为你的项目路径
      args: [
        "--exchange",
        "aster",
        "--market-type",
        "perp",
        "--symbol",
        "SOLUSDT",
        "--strategy",
        "standard",
        "--spread",
        "0.04", // 0.04% 价差
        "--quantity",
        "0.5", // 0.5 SOL 每单
        "--max-orders",
        "2", // 2对订单
        "--target-position",
        "0", // 目标中性持仓
        "--max-position",
        "10", // 最大持仓 10 SOL
        "--position-threshold",
        "2", // 持仓偏离 2 触发调整
        "--inventory-skew",
        "0.15", // 库存偏移 15%
        "--stop-loss",
        "5", // 止损 -5 USDC
        "--take-profit",
        "25", // 止盈 +25 USDC
        "--duration",
        "3600", // 运行 1 小时
        "--interval",
        "10", // 10 秒调整一次
        "--enable-db", // 启用数据库记录
      ],

      // 环境变量
      env: {
        DISABLE_CONTROL_PANEL: "true",
        PYTHONUNBUFFERED: "1",
      },

      // 进程管理
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_restarts: 30, // 因为 duration 短，增加重启次数
      min_uptime: "10s",
      restart_delay: 5000,
      exp_backoff_restart_delay: 100,

      // 日志管理
      error_file: "./logs/aster_sol_perp_err.log",
      out_file: "./logs/aster_sol_perp_out.log",
      log_file: "./logs/aster_sol_perp_combined.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,

      // 自动重启时间（每小时重启，因为 duration=3600）
      cron_restart: "0 * * * *",

      // 监控
      time: true,

      // 错误处理
      kill_timeout: 5000,
      listen_timeout: 3000,
      shutdown_with_message: false,
    },
  ],
};
