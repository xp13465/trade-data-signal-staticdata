# large-json 备份清单(large-json-backup-manifest)

> 由 `scripts/upload_r2.py upload-large-json` 自动生成(2026-09-27), 勿手改。

## 机制一句话

staticdata 备份仓库 7 个 >20MB JSON(共 ~319MB)已移出 git 跟踪(备份天天 `skip_oversize`
不 commit 的根因), 改走 R2 私有桶 `signal-backup` 的 `large-json/` 前缀版本化快照。

- key 格式: `large-json/<YYYY-MM-DD>/<相对 data/ 的路径>.gz`
  - 例: `large-json/2026-09-25/signal_kelly_trades.json.gz`
  - 例: `large-json/2026-09-25/signal_kelly_trades_parts/t2025.json.gz`
- 保留档位: 日档 14 天 + 周档(周日那份) 8 周 + 月档(每月 1 号那份) 12 个月
- 恢复: `bash scripts/restore-large-json.sh <文件名|--list|--date YYYY-MM-DD|--all> [--target <dir>]`
  还原时先下同目录 `.tmp` 再原子覆盖, 覆盖前旧文件备份为 `<文件>.bak-<时间戳>`; 本清单
  有 sha256 记录的会比对, 不匹配即中止(不改原文件)。默认还原目标 = 生产数据目录
  `trade-data/data/`(`STATICDATA_REPO`/`--target` 可覆盖, 非默认目录会打醒目警告)。
  (详见 `docs/backup-restore.md` 第八节)。
- 相关脚本: `scripts/upload_r2.py`(上传) / `scripts/restore-large-json.sh`(恢复入口)。

## 快照明细

| 相对 data/ 路径 | 完整字节 | sha256 | 最新 R2 key | 保留档位 | 生成时间 |
|---|---|---|---|---|---|
| accum_nav_map.json | 26181355 | 9fa1cb91ebf93b0d820e4a8417288a2d0f63458e1311c11e2c9e21964cf1f164 | `large-json/2026-09-27/accum_nav_map.json.gz` | 日+周 | 2026-09-27 |
| offshore_fund_fee_detail.json | 21713076 | 0d98973e65925fc86a7eec553c6037d00444dd0c292c9c992bc2319c08815710 | `large-json/2026-09-27/offshore_fund_fee_detail.json.gz` | 日+周 | 2026-09-27 |
| offshore_fund_performance.json | 40531280 | 48197816fc88de51054f712da118956ed09d43b004abbeb598191c951392b588 | `large-json/2026-09-27/offshore_fund_performance.json.gz` | 日+周 | 2026-09-27 |
| offshore_fund_purchase_status.json | 34272288 | c82a7e57698fe982929bebd87581fe6a28e00155d2919e897bb8c9f380affdd3 | `large-json/2026-09-27/offshore_fund_purchase_status.json.gz` | 日+周 | 2026-09-27 |
| offshore_fund_risk_indicator.json | 22394747 | 717a029010f753c5e063e63c98c02642d2e706feab19007b53798e54867debb4 | `large-json/2026-09-27/offshore_fund_risk_indicator.json.gz` | 日+周 | 2026-09-27 |
| signal_kelly_trades.json | 86586298 | 906163336871d48b3e5c084ec7951e0b0819fc06bfc0a021bae4b3c20d314970 | `large-json/2026-09-27/signal_kelly_trades.json.gz` | 日+周 | 2026-09-27 |
| signal_kelly_trades_sdc.json | 87728074 | 55c60ace60d7c21faa954a1460a17b65f05474cae12e358054fcadcbe03afa9b | `large-json/2026-09-27/signal_kelly_trades_sdc.json.gz` | 日+周 | 2026-09-27 |
| trade_sim/trade_sim_cgb_idx_full.json | 20229144 | fa6b46f1a87ec21a51de9af20d0365598acc9adb107ec9a0ec6139c02a14c429 | `large-json/2026-09-27/trade_sim/trade_sim_cgb_idx_full.json.gz` | 日+周 | 2026-09-27 |
