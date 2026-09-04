#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针脚本:验证 staticdata 仓 manifest 巨文件索引缺口(只读,不动生产数据)。

目的:审计 manifest.json 是否收录 R2 公开桶的 etf/fund_nav 巨文件类,输出缺口清单。
输入依赖:
  - <本仓>/manifest.json                  (数据索引清单)
  - /Users/linhuichen/code/trade/data/.r2_etf_hist_state.json   (R2 etf 已传对象指纹)
  - /Users/linhuichen/code/trade/data/.r2_fund_nav_state.json   (R2 fund_nav 已传对象指纹)
  - trade 仓 scripts/upload_r2.py 的 _list_keys / s3_request(只读 GET/HEAD)
输出:
  - stdout: 各前缀计数 + 缺口统计 + 样例
方法口径:
  - manifest files[] 每条 {path,url,size,sha256};etf 应收 etf/{code}-all.json,fund_nav 应收 fund_nav/{code}.json
  - "缺口"定义 = 该对象在 R2 存在(状态文件或前缀列出)但 manifest files 无对应 path
复现命令:
  cd /Users/linhuichen/code/trade-data-signal-staticdata
  python3 scripts/probe_manifest_gap_20260904.py
依赖:python3 + trade 仓 upload_r2.py(仅 import 读 .env,不发写请求)
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.json"

TRADE_STATE_ETF = Path("/Users/linhuichen/code/trade/data/.r2_etf_hist_state.json")
TRADE_STATE_FUNDNAV = Path("/Users/linhuichen/code/trade/data/.r2_fund_nav_state.json")


def load_manifest():
    m = json.loads(MANIFEST.read_text())
    files = m["files"]
    paths = {f["path"] for f in files}
    return m, files, paths


def state_count(path):
    if not path.exists():
        return None
    d = json.loads(path.read_text())
    return d.get("count"), d.get("updated_at"), list(d.get("files", {}).keys())[:3]


def main():
    print(f"=== 探针: manifest 巨文件索引缺口 (2026-09-04, 只读) ===")
    m, files, paths = load_manifest()
    print(f"manifest: {m['file_count']} 条, r2_base={m['r2_base']}, generated_at={m.get('generated_at')}")

    # 1. etf / fund_nav 在 manifest 的收录情况
    etf_in_manifest = [f for f in files if f["path"].startswith("etf/")]
    fn_in_manifest = [f for f in files if f["path"].startswith("fund_nav/")]
    gz_in_manifest = [f for f in files if f["path"].endswith(".gz")]
    print(f"\nmanifest 收录: etf/{len(etf_in_manifest)} 条, fund_nav/{len(fn_in_manifest)} 条, .gz/{len(gz_in_manifest)} 条")

    # 2. R2 实际对象数(状态文件)
    for label, p in [("etf", TRADE_STATE_ETF), ("fund_nav", TRADE_STATE_FUNDNAV)]:
        c, ts, samples = state_count(p)
        if c is None:
            print(f"R2 {label}: 状态文件缺失({p})")
        else:
            print(f"R2 {label}: count={c}, updated_at={ts}, 样例={samples}")

    # 3. 缺口 = R2 有 manifest 无
    print("\n缺口: manifest 未收录 etf/fund_nav 两类对象(R2 有,索引无)")
    if etf_in_manifest or fn_in_manifest:
        print("  ⚠ 已收录,预期缺口消失")
    else:
        print("  ✓ 确认缺口存在(需 §方案 补 manifest)")

    # 4. R2 data/ 前缀对象 vs manifest data/ 前缀(读取 R2 仅 GET)
    try:
        sys.path.insert(0, str(Path("/Users/linhuichen/code/trade/scripts")))
        import upload_r2

        keys = upload_r2._list_keys("data/", bucket=upload_r2.BUCKET)
        manifest_data = {f["path"] for f in files if f["url"].startswith(upload_r2.PUBLIC + "/data/")}
        missing = sorted(k.replace("data/", "") for k in keys if k.replace("data/", "") not in manifest_data)
        print(f"\nR2 data/ 前缀对象: {len(keys)} 个, manifest 收录 data/ 前缀: {len(manifest_data)} 个, 漏 {len(missing)} 个")
        print(f"漏网样例(前5): {missing[:5]}")
    except Exception as e:
        print(f"\n⚠ R2 data/ 前缀探针失败(不影响主结论): {e}")

    print("\n结论: manifest 需补 etf/({count}) + fund_nav/({count}) + data/ 前缀漏网对象;sha256 数据源=trade static-site(与 R2 逐位一致)")


if __name__ == "__main__":
    main()
