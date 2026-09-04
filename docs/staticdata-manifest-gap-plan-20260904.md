# staticdata 仓「巨文件索引缺口」补全方案

- 日期:2026-09-04
- 审计背景:主控 2026-09-04 对账发现 manifest.json 未收录 etf / fund_nav / .gz 三类对象;本方案给出补全设计（只出方案+探针验证,不实施改造）
- 数据仓:trade-data-signal-staticdata（独立 git 仓,与 trade 主仓无关）

## 〇、探针验证结论(只读,未动任何生产数据)

本方案所有结论均基于只读探针,证据点如下:

### 1. manifest.json 现有结构(174KB,857 条,generated_at 2026-08-10)

顶层 keys:`generated_at / description / data_license / third_party_notice / r2_base / file_count / total_size / files / databases`

files 条目结构(现网样例):
```json
{"path":"trade_sim/trade_sim_bj50_full.json","url":"https://ssd.fx8.store/trade_sim_data/trade_sim_bj50_full.json","size":1010372,"sha256":"bdbee41b1a0a073a322b75af2b797cecfe74a1d6fda40b16a636185b2c2fd26f"}
{"path":"index/bj50-all.json","url":"https://ssd.fx8.store/index/bj50-all.json","size":158981,"sha256":"79e44a700cc551a2d474c321ddba3002159087b61714efaea209bd09570ad1fb"}
```

databases 段(4 条,DB 归档放 GitHub Release):
```json
{"name":"sentiment.db.tar.gz","description":"...","url":"https://github.com/xp13465/trade-data-signal-staticdata/releases/download/db-archive-2026-08-10/sentiment.db.tar.gz","size":37396124,"sha256":"37e99de0a5ff4d60459a7a9894b35108e523bfa1593e61ba85653e0dd9833201","uploaded":true}
```

files 按 R2 URL 前缀分布:data/ 137 · trade_sim_data/ 334 · index/ 165 · industry/ 134 · lab/ 65 · public_fund/ 13 · offshore_fund/ 7 · fund_score/ 2

### 2. R2 对象前缀探针(只读列出 + HEAD)

上传机制在 trade 仓 `scripts/upload_r2.py`:
- etf 前缀:`cmd_upload_etf_hist` → R2 key = `etf/{code}-all.json`(1546 只全史日K,本地 `static-site/data/etf/`)
- fund_nav 前缀:`cmd_upload_fund_nav` → R2 key = `fund_nav/{code}.json`(26239 只全史净值,本地 `static-site/data/fund_nav/`)

探针验证 URL 模式(HTTP 200):
```
https://ssd.fx8.store/etf/158000-all.json      → 200 ETag=277601a8...
https://ssd.fx8.store/fund_nav/000001.json     → 200 ETag=6b22fedb...
https://ssd.fx8.store/data/board_etf_map.json  → 200
```

R2 对象总数(来自 upload_r2 状态文件,精确):
- `data/.r2_etf_hist_state.json`:count=1546,files 名→md5 指纹,updated_at 2026-09-03
- `data/.r2_fund_nav_state.json`:count=26239,files 名→md5 指纹,updated_at 2026-09-03
- 这两个状态文件本身就是「当前 R2 已传对象的精确清单」,是 manifest 生成的现成数据源(比扫本地目录更可靠)

### 3. 关键发现一:staticdata 仓 git 其实「已双写」但「未索引」

- `git ls-files`:data/etf=1546、data/fund_nav=26239、顶层 json=28659、data/index=173、data/lab=65
- 根因:`deploy.sh L697-713` rsync 全量 `static-site/data/` 到 staticdata 仓 data/ 后 `git add -A` 全提交
- 含义:任务背景「etf/fund_nav 只存 R2 不进 manifest」的准确表述应为:**R2 分发 + staticdata git 双写已完成,但 manifest.json 未索引这两类(和 R2 data/ 前缀下 428 个未收录对象)→ fetch_data.sh 无法一键还原**
- 附带问题:staticdata 仓 `.git` 已达 2.1G。deploy 每次全量 rsync 会把当日整目录快照进 git(非差异),etf/fund_nav 全量双写进 git 与「大文件走 R2」架构初衷相悖——**这是本方案需一并上报的方向性问题**(详见 §8 风险5)

### 4. 关键发现二:staticdata 仓内副本滞后一天

- staticdata 仓 `data/fund_nav/000001.json` mtime=09-03 18:58,而 trade `static-site/data/fund_nav/000001.json` mtime=09-04 19:34,R2 对应对象 ETag 与 trade 侧一致
- 结论:
  1. R2 与 trade 主仓 `static-site/data/` 最新内容**逐位一致**(同源同批次上传),R2 是可信最新源
  2. staticdata 仓内快照是 deploy 时点残留,**滞后不等于错误**,但**不能作为 manifest sha256 的数据源**
  3. manifest 补 etf/fund_nav 的 sha256 必须取 trade `static-site/data/` 或直接 R2 对象,**不能扫 staticdata 仓本地 data/**

### 5. 关键发现三:映射文件是否一并收录(判断结论)

探针在 R2 各前缀下检索 etf_index_map/etf_track/lof_track/fund_score_list:
- `etf_index_map.json` / `etf_track_index.json` / `lof_track_index.json`:仅存在于 trade `data/`(构建期派生映射),**不在 R2 公开桶** → 属内部构建输入,不进 manifest
- `accum_nav_map.json`(19MB):staticdata 仓 data/ 与 R2 data/ 前缀均有,**当前在「R2 有而 manifest 无」的 428 个未收录清单里** → 应一并补进 manifest(data/ 前缀)
- `fund_score.json` / `fund_score_top.json`:R2 `fund_score/` 前缀已有 2 个对象,manifest 已收 2 条 → 无缺口
- .gz:R2 data/ 前缀仅 1 个 `.gz`(signal_kelly_backtest.json.gz),etf/fund_nav 无 .gz;staticdata 本地 75 个 .gz 大多未上 R2。判断:**只索引 R2 实际存在的对象**,不把本地 gz 当必须收(避免了 1 万个 gz 全塞进 manifest 的膨胀)

### 6. 探针验证用品(全部只读)

```bash
# R2 前缀 + 对象列表(只读)
.venv/bin/python scripts/upload_r2.py list "etf/"       # 前 100 key
.venv/bin/python scripts/upload_r2.py list "fund_nav/"
# 状态文件(精确对象清单)仅读取
python3 -c "import json;d=json.load(open('data/.r2_fund_nav_state.json'));print(d['count'])"
```

---

## 一、manifest 补全 JSON schema 设计

### 1.1 新增 `files` 条目(与现有 trade_sim/index 条目结构完全对齐,不改现有字段)

现有条目 5 字段:`path / url / size / sha256`。etf/fund_nav 用同一 schema,只新增条目,不新增顶层结构,保持 fetch_data.sh 零改动兼容:

```json
// etf(样例,R2 校验 sha256 已验证编者实测一致)
{"path":"etf/158000-all.json","url":"https://ssd.fx8.store/etf/158000-all.json","size":704,"sha256":"9e5d2c7a38c0c9471346cf942a9d1c6161f39a1502ec3282abed2b390ca56a26"}
{"path":"etf/510300-all.json","url":"https://ssd.fx8.store/etf/510300-all.json","size":300721,"sha256":"9c3ca95b3f3f7aa377b1699fceb8c998b3a590b3235017f463934137d3595592"}

// fund_nav(样例)
{"path":"fund_nav/000001.json","url":"https://ssd.fx8.store/fund_nav/000001.json","size":29957,"sha256":"ec9e9cd75b0f6a46a6d9835443b365311ab2c7ca627acb8e0d8aa5de166a57fd"}
{"path":"fund_nav/000003.json","url":"https://ssd.fx8.store/fund_nav/000003.json","size":29968,"sha256":"28f4b662ac061147eddc3d460786a3b755e5ab03c9dd31c3c4025d0cf7573542"}

// data/ 前缀漏网对象(428 个未收录之代表,建议一并补)
{"path":"accum_nav_map.json","url":"https://ssd.fx8.store/accum_nav_map.json","size":19146546,"sha256":"ad49fbbd7b11ec564bcc2eaf971646bbbb7131080800ffc86ec8a65fb4ebaf6b"}
{"path":"signal_kelly_backtest.json.gz","url":"https://ssd.fx8.store/data/signal_kelly_backtest.json.gz","size":123456,"sha256":"..."}
```

### 1.2 URL 前缀映射(关键,防错配)

`gen_data_manifest.py` 现 `r2_key_for()` 全量映射规则:
```
data/*.json → data/{rel}(顶层 + 未映射子目录)
industry-* → industry/ · public_fund* → public_fund/ · offshore_fund* → offshore_fund/
fund_score* → fund_score/ · index/* → index/ · lab/* → lab/ · trade_sim/* → trade_sim_data/
```

**注意 trade_sim 的坑**:本地子目录 `trade_sim/` 上传前缀是 `trade_sim_data/`(避开同名 HTML 前缀)。etf/fund_nav 无此冲突,**直接 `etf/{name}` / `fund_nav/{name}`**:
```python
def r2_key_for(rel: str) -> str:
    ...
    if rel.startswith("etf/"):
        return f"etf/{Path(rel).name}"
    if rel.startswith("fund_nav/"):
        return f"fund_nav/{Path(rel).name}"
    return f"data/{rel}"
```

### 1.3 新增条目数据源(三选一,推荐 B)

- **方案 A 扫 staticdata 本地 data/**:❌ 已证滞后一天,sha256 对不上 R2 → **弃**
- **方案 B 扫 trade 主仓 `static-site/data/`(推荐)**:与 R2 逐位一致(探针已证 4 个对象 ETag 全对齐),sha256 可信,一行生成
- **方案 C 直接读 R2 状态文件 `data/.r2_fund_nav_state.json`**:md5 指纹 ≠ sha256(manifest 要 sha256),需重新 HEAD/GET 才可复用,不如 B 直接

**结论:manifest 生成脚本读 `REPO/static-site/data/`(REPO=trade 主仓),或生成前先 rsync 同步一次再扫。**

### 1.4 databases 段是否需要扩

不需要。databases 段已含 4 个 DB Release 条目;etf/fund_nav 是 JSON 数据产物,归 files 段。新增一个可选的 `r2_note` 顶层字段注明「etf/fund_nav 属巨文件类,网关/R2 直链」便于阅读即可,不影响解析。

---

## 二、fetch_data.sh 扩展方案

### 2.1 现状(4381B)
- 读 manifest `files` 数组,逐条 `path<TAB>url<TAB>sha256` 下载到 `data/{rel}`
- 已有能力:跳过已存在且 sha256 匹配、失败重试 3 次、`--resume`(curl -C -)、`--sample=N` 抽样
- **问题**:manifest 没有 etf/fund_nav → fetch 扫不到这两类 → 无法一键还原

### 2.2 扩展点(最小改动)

**① 默认支持 etf/fund_nav(零代码)**
manifest 补条目后 fetch_data.sh 天然可下载(同一 `files` 数组),路径落 `data/etf/*.json`、`data/fund_nav/*.json`。**验证即可,不必改。**

**② 超大文件分片/续传(推荐加 `--chunk` + `--resume` 增强)**
- etf/fund_nav 单文件最大 ~450KB/33KB,总量 660MB,共 27785 文件。单文件不算"巨"(巨在 count),curl 直下 30 秒/个内可完成
- 但**整体 2.8 万次请求**串行较慢,建议:
  - `--parallel N`:xargs -P 8 并行下载(幂等:每文件独立校验,互不影响)
  - `--chunk`:为将来 >100MB 单文件预留 Range 分段(curl `-r`),现在不需要,留接口
  - `--resume` 已存在:断线 `curl -C -` 续传,校验仍以 sha256 为准
- 验证:下载后 sha256 逐文件校验(现有逻辑已保证)

**③ 抽样加速(已有 `--sample=N`)**
改 manifest 全量后,`--sample` 语义保持(从全量 files 随机抽 N)——2.8 万条里抽 5 条验证两类都可下,用于 CI/自验。

### 2.3 注意(fetch 与 upload 一致性)
- R2 key 必须与 upload 侧完全一致:`etf/{code}-all.json`、`fund_nav/{code}.json`(不是 `data/etf/...`)
- `.r2_*_state.json` 的 md5 指纹 ≠ manifest sha256,两者用途不同(前者上传增量判断,后者下载校验),不混用

---

## 三、「一键还原脚本」设计

### 3.1 结论:扩展 fetch_data.sh,不新建还原脚本

| 现有脚本 | 定位 | 是否适合本次 |
|---|---|---|
| `fetch_data.sh` | 一键全量复原(读 manifest 下载全部) | ✅ **就是还原脚本,manifest 补齐后自动覆盖 etf/fund_nav** |
| `restore-r2-backup.sh` | 从私有桶 `signal-backup/decommissioned/` 还原退役归档 | ❌ 改它是把「退役清理专用」与「全量还原」职责混淆,不扩展 |
| `backup_db.sh` | 本地 SQLite 热备到 data/backups/ | 无关(DB 层) |
| `verify_backup.sh` | R2 备份恢复演练(DB 层) | 无关(DB 层),但可借鉴其「定期演练确认可恢复」思路 |
| `release_db.sh` | DB 归档打包上传 GitHub Release | 无关 |

还原路径:manifest `files` 的 path 相对 `data/`,fetch 下载到 `data/{path}` → 落位 `data/etf/` + `data/fund_nav/`。校验 sha256(现有)。幂等:已存在且 sha256 匹配自动跳过;失败重试 3 次;`--resume` 断点续传。

### 3.2 建议新增一个薄封装 `restore-large-files.sh`(可选,不新增适用)

给用户一个显式入口,避免先跑 manifest 全量(2.8 万文件)再拉巨文件:
```bash
#!/usr/bin/env bash
# 只还原 etf/fund_nav 巨文件类(增量,幂等)
# 用法: bash scripts/restore-large-files.sh [--resume]
python3 - scripts <<'PY'
import json, subprocess, sys
m = json.load(open('manifest.json'))
targets = [f for f in m['files'] if f['path'].startswith(('etf/','fund_nav/'))]
# 输出 path<tab>url<tab>sha256 交给 fetch_data.sh 的循环逻辑(或复用其主循环)
PY
```
- 判据:`startswith(('etf/','fund_nav/'))` 依赖 §1.1 的 path 前缀约定
- 也可直接用 `bash fetch_data.sh --categories=etf,fund_nav`(若实现 `--categories` 过滤参数,则无需新脚本)

### 3.3 与 backup/verify 的关系(一图讲清)

- backup_db.sh / verify_backup.sh / release_db.sh = **DB 层**(私有桶/Release)
- fetch_data.sh / restore-large-files.sh = **JSON 层公开分发**(R2 公开桶)
- manifest = JSON 层的「唯一索引」(files = 分发清单,databases = DB 清单)
- 建议:verify 演练(周期性抽 N 个 manifest 条目 sha256 校验)下沉到 fetch_data.sh `--sample`,复用现有抽样,不新建 verify 脚本

---

## 四、落地实施步骤清单(分步 + 每步验证点)

> 本方案不实施,以下为未来实施时的执行清单。

| # | 步骤 | 关键动作 | 验证点 |
|---|---|---|---|
| 1 | 确认数据源 | `REPO=/Users/linhuichen/code/trade` 确认 `static-site/data/etf`、`static-site/data/fund_nav` 存在且与 R2 ETag 一致 | `diff <(curl -sI https://ssd.fx8.store/etf/510300-all.json <grep etag) <(md5 local)` 逐位对 |
| 2 | 改 `gen_data_manifest.py` | `r2_key_for()` 加 etf/{name}、fund_nav/{name} 分支(§1.2),数据源改读 `REPO/static-site/data/`(§1.3-B) | 单测:`r2_key_for('etf/158000-all.json') == 'etf/158000-all.json'`;`python3 gen_data_manifest.py` 后 grep 新条目 url 前缀正确 |
| 3 | 跑 manifest 生成 | 生成新 manifest,确认 file_count 从 857 → ~28,500+(27785 etf/fund_nav + data/ 前缀补漏 428) | `python3 -c "json.load(open('manifest.json'))['file_count']"`;抽查 5 条 url 前缀=etf/fund_nav/data;sha256 与 R2 一致 |
| 4 | 改 fetch_data.sh | 无需改主逻辑;可选 `--parallel N`/`--categories`(§2.2-②) | `bash fetch_data.sh --sample 5`(含 etf/fund_nav 各抽到)全绿 |
| 5 | 全量还原演练 | `bash fetch_data.sh` 到干净目录跑一遍(或 `--categories=etf,fund_nav`) | 27785 文件全部 sha256 通过;耗时记录;幂等重跑 SKIP 全命中 |
| 6 | commit + push | staticdata 仓:manifest.json + gen_data_manifest.py 改动 commit;附本方案文档同 commit | `git ls-files` 确认新文件 tracked;push 成功 |
| 7 | 定期刷新 | manifest 生成进 cron(如每周日 22:00 后与 update_all 错开) | 定时产物 sha256 抽查即 fetch_data.sh --sample 每轮绿 |

## 五、风险与规避

| # | 风险 | 影响 | 规避 |
|---|---|---|---|
| 1 | manifest 从 174KB → 数十 MB(file_count 2.8 万+) | fetch_data.sh 每次解析 + 任务行生成变慢;github 仓变大 | 可接受(2.8 万行 JSON 解析 <1s);不把 .gz 全收;`--sample` 是默认验证路径 |
| 2 | staticdata 仓内副本滞后(探针证)导致 sha256 错配 | 用户按 manifest 下载 sha256 失败 | §1.3 强制从 trade static-site 最新源生成;fetch 端 sha256 校验会拦错(防静默坏数据) |
| 3 | etf/fund_nav 前缀与 upload_r2 漂移(如换前缀) | manifest URL 404 | `gen_data_manifest.py` 加 URL HEAD 抽查(现有 `--verify` 已支持),CI 挂 manifest 全量 HEAD 或抽样 |
| 4 | trade_sim_data 前缀历史坑 | 若未来 etf 也出现同名 HTML 前缀冲突,url 会错 | 生成脚本按 §1.2 显式映射,不自动推断 |
| 5 | **staticdata 仓 .git 2.1G 且 etf/fund_nav 全量双写进 git**(方向性问题) | 与「巨文件走 R2」架构初衷相悖,deploy 全量 rsync 每次放大仓;git 推送慢/可能超 GitHub 单文件限制 | **不在本方案擅自改**。上报主控:是否将 etf/fund_nav 从 rsync+git add 中排除(改 .gitignore/rsync exclude),只留 manifest 索引+R2 分发;排除后 .git 可持续瘦身。本方案只补索引不删文件 |
| 6 | .r2_*_state.json md5 ≠ sha256 | 若误把状态文件当 manifest 数据源会 sha256 对不上 | §1.3 明确三选一选 B,状态文件只用于上传增量,不喂 manifest |

## 六、落档与归属

- 方案文档:trade-data-signal-staticdata 仓 `docs/staticdata-manifest-gap-plan-20260904.md`(本文件)
- 理由:方案改动的对象(manifest.json/gen_data_manifest.py/fetch_data.sh)全在该仓;trade 主仓当前 feat 分支 sigkelly-review2 在审、禁止 commit,落 staticdata 仓独立显式,不混主仓 merge 链
- 探针脚本:只读命令已在 §〇.6 提供,不落独立脚本文件(避免新增无用代码,复用 upload_r2.py list 能力)

## 复现

```bash
# 1. 探针:读 manifest 结构 + 前缀(只读)
cd /Users/linhuichen/code/trade-data-signal-staticdata
python3 - <<'PY'
import json
m=json.load(open('manifest.json'))
print(m['file_count'], len(m['files']), m['r2_base'])
print(m['files'][0])
PY

# 2. 探针:R2 etf/fund_nav 前缀 + URL 可用性(只读)
cd /Users/linhuichen/code/trade
.venv/bin/python scripts/upload_r2.py list "etf/"        # 状态200,列出 etf/158000-all.json 等
.venv/bin/python scripts/upload_r2.py list "fund_nav/"   # 状态200,列出 fund_nav/000001.json 等
curl -s -o /dev/null -w '%{http_code}\n' -I https://ssd.fx8.store/etf/510300-all.json   # 200
curl -s -o /dev/null -w '%{http_code}\n' -I https://ssd.fx8.store/fund_nav/000001.json  # 200

# 3. 状态文件(精确对象清单,只读)
python3 -c "import json,os;d=json.load(open('/Users/linhuichen/code/trade/data/.r2_etf_hist_state.json'));print('etf',d['count'])"
python3 -c "import json,os;d=json.load(open('/Users/linhuichen/code/trade/data/.r2_fund_nav_state.json'));print('fund_nav',d['count'])"

# 4. R2 与 trade static-site 一致性(逐位对账,4 对象探针已 PASS)
python3 - <<'PY'
import hashlib
for p in ['/Users/linhuichen/code/trade/static-site/data/etf/510300-all.json']:
    h=hashlib.md5(open(p,'rb').read()).hexdigest(); print(p.split('/')[-1], h)
PY
#   对照:curl -sI https://ssd.fx8.store/etf/510300-all.json | grep -i etag → a9384ddcab5ca23dca688c269a0a5b4e(与现网一致)

# 关键口径一句话:
#   manifest 补 etf (R2 key=etf/{code}-all.json) + fund_nav (R2 key=fund_nav/{code}.json),
#   sha256 数据源必须取 trade static-site/data(与 R2 逐位一致),不能扫 staticdata 仓本地 data/.
```

---

## 附:探针证据链(2026-09-04,只读)

| 探针 | 结果 |
|---|---|
| manifest file_count / files len / r2_base | 857 / 857 / https://ssd.fx8.store |
| R2 etf/ 前缀列表 | status=200,含 etf/158000-all.json 等 |
| R2 fund_nav/ 前缀列表 | status=200,含 fund_nav/000001.json 等 |
| URL HEAD | etf/158000-all.json=200(790B)、fund_nav/000001.json=200、data/board_etf_map.json=200 |
| 状态文件 etf | count=1546,updated_at 2026-09-03 |
| 状态文件 fund_nav | count=26239,updated_at 2026-09-03 |
| staticdata git 跟踪 | data/etf=1546、data/fund_nav=26239、data/index=173 |
| R2 vs trade static-site md5 | etf/510300 ETag a9384ddc == 本地 md5(逐位一致,PASS) |
| R2 data/ 前缀对象 vs manifest | R2=565 个,manifest 只收 137 个,428 个漏(accum_nav_map.json 为代表) |
| R2 data/ 下 .gz | 仅 signal_kelly_backtest.json.gz(1 个) |
| 映射文件 etf_index_map/etf_track/lof_track | 不在 R2 公开桶(仅 trade data/ 内部) |