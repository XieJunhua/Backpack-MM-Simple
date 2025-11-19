module.exports = {
  apps: [
    {
      name: "sol_perp_mm",
      script: "run.py",
      interpreter: "python3",
      cwd: "/root/github/Backpack-MM-Simple",
      args: [
        "--exchange",
        "backpack",
        "--market-type",
        "perp",
        "--symbol",
        "SOL_USDC_PERP",
        // "--strategy", "standard", // 如果报错 unrecognized arguments，请删除此行

        // --- 核心交易参数 ---
        "--spread",
        "0.06", // [修正] 填 0.06 代表 0.06%。足以覆盖约 0.04% 的来回手续费
        "--quantity",
        "0.3", // 每单 0.3 SOL
        "--max-orders",
        "2", // 上下各挂 2 单

        // --- 仓位管理 ---
        "--target-position",
        "0",
        "--max-position",
        "1.5",
        "--position-threshold",
        "0.9",
        "--inventory-skew",
        "0", // 建议开启库存倾斜

        // --- 风险控制 ---
        "--stop-loss",
        "10",
        "--take-profit",
        "10",

        // --- 运行设置 ---
        "--duration",
        "86400",
        "--interval",
        "10",
        "--enable-db",
      ],

      // 环境变量
      env: {
        DISABLE_CONTROL_PANEL: "true",
        WEB_HOST: "0.0.0.0",
        WEB_PORT: "5000",
        PYTHONUNBUFFERED: "1",
      },

      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_restarts: 20,
      restart_delay: 5000,

      error_file: "./logs/sol_perp_mm_err.log",
      out_file: "./logs/sol_perp_mm_out.log",
      log_file: "./logs/sol_perp_mm_combined.log",
      merge_logs: true,
    },
  ],
};
