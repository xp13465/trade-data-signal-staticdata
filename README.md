# 📦 tdsignal 数据开源仓库 · trade-data-signal-staticdata

> [tdsignal 市场温度看板](https://github.com/xp13465/trade-data-signal) 的**全量数据开源门面**：
> A股 / 港股 / 全球 情绪指数、市场宽度、买卖点信号、行业/概念、ETF 国家队资金动向等
> 每日盘后采集产出的 JSON 数据产物与原始 SQLite 数据库，**全部对外开放、可复用**。

**代码仓库（看板本体）**：<https://github.com/xp13465/trade-data-signal> —— 本仓库只放数据 + 还原工具，
代码（采集 / 计算 / 前端 / 部署）在开发库。

**在线体验**：<https://ss.fx8.store/>

---

## 一、数据种类与规模

| 类别 | 内容 | 规模 |
|---|---|---|
| JSON 数据产物 | 情绪指数历史（sentiment-*）/ A股 32 指标 + 宽基 OHLC（a-stock-*）/ 港股 / 全球 / 行业与概念 / ETF 国家队 / 期货持仓 / 收盘速递 / 盘中快照 / 44 指数全历史 等 | **857 个文件 / 约 943MB** |
| 原始 SQLite 数据库 | `sentiment.db` / `etf_national_team.db` / `stock_daily.db` / `public_fund.db`（打包 tar.gz） | GitHub Release 下载 |

- **数据清单**：见根目录 [`manifest.json`](manifest.json)（每项含 `path` / `url`（R2 直链）/ `size` / `sha256` 完整性校验）
- **字段说明**：见开发库 [docs/data-dictionary.md](https://github.com/xp13465/trade-data-signal/blob/main/docs/data-dictionary.md)
- **数据源与采集时点**：见开发库 [docs/data-sources.md](https://github.com/xp13465/trade-data-signal/blob/main/docs/data-sources.md)

## 二、授权

- **数据集**：[CC BY 4.0](DATA_LICENSE)（可共享 / 改编 / 商用，需署名）
- **第三方声明**：[NOTICE](NOTICE)（原始行情来自第三方公开数据源，本仓库授权不覆盖第三方原始数据版权）

## 三、如何还原全量数据

```bash
git clone https://github.com/xp13465/trade-data-signal-staticdata.git
cd trade-data-signal-staticdata
bash fetch_data.sh        # 按 manifest.json 从 R2 公开桶下载全部 JSON（约 1GB，可重复跑，已下载自动跳过）
```

- **下载源**：R2 公开桶 `https://ssd.fx8.store/`（Cloudflare R2 CDN，无鉴权直链，大 range 历史文件与行业/概念拆分也走对应前缀）
- **可选**：原始 SQLite 库在 GitHub [Releases](https://github.com/xp13465/trade-data-signal-staticdata/releases)（tag `db-archive-*`），URL 与 sha256 见 `manifest.json` 的 `databases` 字段
- 在线按需拉取单个文件（无需 clone）：`curl -o overview.json https://ssd.fx8.store/data/overview.json`

## 四、本仓库结构

```
config/            # launchd 定时任务 plist 模板（脱敏）+ wrangler.jsonc + .env.example
data/              # 全量 JSON 数据产物（git 内为小 JSON 差异日志；大文件/压缩文件走 R2，.gitignore 排除）
db/                # 原始 SQLite 数据库（本地备份，>100MB 不进 git，由 R2 私有桶 gz 快照备份）
manifest.json      # 全量 JSON 索引清单（fetch_data.sh 读取；数据更新后用 gen_data_manifest.py 重新生成）
fetch_data.sh      # 一键全量复原脚本（从 R2 下载全部 JSON + sha256 校验）
gen_data_manifest.py  # 重新生成 manifest.json
release_db.sh      # 把 SQLite 数据库归档包上传到本仓库 GitHub Release
DATA_LICENSE       # 数据集 CC BY 4.0 授权
NOTICE             # 第三方数据源声明
```

## 五、数据更新机制

- 每日盘后（约 17:50 起）开发库 `deploy.sh` 自动把最新 JSON / DB 备份到本仓库并 `commit + push`（best-effort，失败不阻断）
- 盘中每 15 分钟 `intraday_snapshot.json` 实时快照走 R2 直链（不进本仓库 git）
- 大文件 / 压缩文件只走 R2 公开桶（本仓库 git 的 `.gitignore` 排除 `index-*` / `industry-*` / `lab-*` / `trade_sim_*` / `*.gz`），保证仓库轻量

---

## ⚠️ 声明

本数据仅供学习研究，**不构成投资建议**。买卖点信号为历史回测参考，胜率接近随机，不可作为独立交易依据。
数据准确性受数据源限制，请以官方披露为准。
