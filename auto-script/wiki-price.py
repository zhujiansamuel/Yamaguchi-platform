import re
import requests
import asyncio
from typing import Optional, Tuple, List, Dict
import pandas as pd
from playwright.async_api import async_playwright

# 全局变量定义
df2 = None

BASE_URL = "http://www.mobile-zone.jp"
TOKEN = "008c43ec-7b08-4af0-86c4-b4495e15cee0"
LIST_ENDPOINT = f"{BASE_URL}/api/goodsprice/list"
UPDATE_ENDPOINT = f"{BASE_URL}/api/goodsprice/update"
PRICE_COL = "未開封_int"
URL = "https://iphonekaitori.tokyo/series/iphone/market-price"
BASE_URL = "http://www.mobile-zone.jp"
reduce_json = [{
    "goods_id": 36,
    "title": "iPhone Air 1TB",
    "category_three_name": "iPhone Air",
    "spec_index": 0,
    "spec_name": "スペースブラック",
    "reduce_price": -1000
},
    {
        "goods_id": 36,
        "title": "iPhone Air 1TB",
        "category_three_name": "iPhone Air",
        "spec_index": 1,
        "spec_name": "クラウドホワイト",
        "reduce_price": -1000
    },
    {
        "goods_id": 36,
        "title": "iPhone Air 1TB",
        "category_three_name": "iPhone Air",
        "spec_index": 2,
        "spec_name": "ライトゴールド",
        "reduce_price": -1000
    },
    {
        "goods_id": 36,
        "title": "iPhone Air 1TB",
        "category_three_name": "iPhone Air",
        "spec_index": 3,
        "spec_name": "スカイブルー",
        "reduce_price": -1000
    },
    {
        "goods_id": 35,
        "title": "iPhone Air 512GB",
        "category_three_name": "iPhone Air",
        "spec_index": 0,
        "spec_name": "スペースブラック",
        "reduce_price": -1000
    },
    {
        "goods_id": 35,
        "title": "iPhone Air 512GB",
        "category_three_name": "iPhone Air",
        "spec_index": 1,
        "spec_name": "クラウドホワイト",
        "reduce_price": -1000
    },
    {
        "goods_id": 35,
        "title": "iPhone Air 512GB",
        "category_three_name": "iPhone Air",
        "spec_index": 2,
        "spec_name": "ライトゴールド",
        "reduce_price": -1000
    },
    {
        "goods_id": 35,
        "title": "iPhone Air 512GB",
        "category_three_name": "iPhone Air",
        "spec_index": 3,
        "spec_name": "スカイブルー",
        "reduce_price": -1000
    },
    {
        "goods_id": 34,
        "title": "iPhone Air 256G",
        "category_three_name": "iPhone Air",
        "spec_index": 0,
        "spec_name": "スペースブラック",
        "reduce_price": -1000
    },
    {
        "goods_id": 34,
        "title": "iPhone Air 256G",
        "category_three_name": "iPhone Air",
        "spec_index": 1,
        "spec_name": "クラウドホワイト",
        "reduce_price": -1000
    },
    {
        "goods_id": 34,
        "title": "iPhone Air 256G",
        "category_three_name": "iPhone Air",
        "spec_index": 2,
        "spec_name": "ライトゴールド",
        "reduce_price": -1000
    },
    {
        "goods_id": 34,
        "title": "iPhone Air 256G",
        "category_three_name": "iPhone Air",
        "spec_index": 3,
        "spec_name": "スカイブルー",
        "reduce_price": -1000
    },
    {
        "goods_id": 33,
        "title": "iPhone 17 512GB",
        "category_three_name": "iPhone 17",
        "spec_index": 0,
        "spec_name": "ブラック",
        "reduce_price": -1000
    },
    {
        "goods_id": 33,
        "title": "iPhone 17 512GB",
        "category_three_name": "iPhone 17",
        "spec_index": 1,
        "spec_name": "ホワイト",
        "reduce_price": -1000
    },
    {
        "goods_id": 33,
        "title": "iPhone 17 512GB",
        "category_three_name": "iPhone 17",
        "spec_index": 2,
        "spec_name": "ミストブルー",
        "reduce_price": -1000
    },
    {
        "goods_id": 33,
        "title": "iPhone 17 512GB",
        "category_three_name": "iPhone 17",
        "spec_index": 3,
        "spec_name": "ラベンダー",
        "reduce_price": -1000
    },
    {
        "goods_id": 33,
        "title": "iPhone 17 512GB",
        "category_three_name": "iPhone 17",
        "spec_index": 4,
        "spec_name": "セージ",
        "reduce_price": -1000
    },
    {
        "goods_id": 32,
        "title": "iPhone 17 256G",
        "category_three_name": "iPhone 17",
        "spec_index": 0,
        "spec_name": "ブラック",
        "reduce_price": 0
    },
    {
        "goods_id": 32,
        "title": "iPhone 17 256G",
        "category_three_name": "iPhone 17",
        "spec_index": 1,
        "spec_name": "ホワイト",
        "reduce_price": 0
    },
    {
        "goods_id": 32,
        "title": "iPhone 17 256G",
        "category_three_name": "iPhone 17",
        "spec_index": 2,
        "spec_name": "ミストブルー",
        "reduce_price": 0
    },
    {
        "goods_id": 32,
        "title": "iPhone 17 256G",
        "category_three_name": "iPhone 17",
        "spec_index": 3,
        "spec_name": "ラベンダー",
        "reduce_price": 0
    },
    {
        "goods_id": 32,
        "title": "iPhone 17 256G",
        "category_three_name": "iPhone 17",
        "spec_index": 4,
        "spec_name": "セージ",
        "reduce_price": 0
    },
    {
        "goods_id": 31,
        "title": "iPhone 17 Pro 512GB",
        "category_three_name": "iPhone 17 Pro",
        "spec_index": 0,
        "spec_name": "シルバー",
        "reduce_price": 0
    },
    {
        "goods_id": 31,
        "title": "iPhone 17 Pro 512GB",
        "category_three_name": "iPhone 17 Pro",
        "spec_index": 1,
        "spec_name": "コズミックオレンジ",
        "reduce_price": 0
    },
    {
        "goods_id": 31,
        "title": "iPhone 17 Pro 512GB",
        "category_three_name": "iPhone 17 Pro",
        "spec_index": 2,
        "spec_name": "ディープブルー",
        "reduce_price": 0
    },
    {
        "goods_id": 30,
        "title": "iPhone 17 Pro 256GB",
        "category_three_name": "iPhone 17 Pro",
        "spec_index": 0,
        "spec_name": "シルバー",
        "reduce_price": 0
    },
    {
        "goods_id": 30,
        "title": "iPhone 17 Pro 256GB",
        "category_three_name": "iPhone 17 Pro",
        "spec_index": 1,
        "spec_name": "コズミックオレンジ",
        "reduce_price": 0
    },
    {
        "goods_id": 30,
        "title": "iPhone 17 Pro 256GB",
        "category_three_name": "iPhone 17 Pro",
        "spec_index": 2,
        "spec_name": "ディープブルー",
        "reduce_price": 0
    },
    {
        "goods_id": 29,
        "title": "iPhone 17 Pro Max 2TB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 0,
        "spec_name": "シルバー",
        "reduce_price": -1000
    },
    {
        "goods_id": 29,
        "title": "iPhone 17 Pro Max 2TB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 1,
        "spec_name": "コズミックオレンジ",
        "reduce_price": -1000
    },
    {
        "goods_id": 29,
        "title": "iPhone 17 Pro Max 2TB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 2,
        "spec_name": "ディープブルー",
        "reduce_price": -1000
    },
    {
        "goods_id": 28,
        "title": "iPhone 17 Pro Max 1TB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 0,
        "spec_name": "シルバー",
        "reduce_price": 0
    },
    {
        "goods_id": 28,
        "title": "iPhone 17 Pro Max 1TB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 1,
        "spec_name": "コズミックオレンジ",
        "reduce_price": 0
    },
    {
        "goods_id": 28,
        "title": "iPhone 17 Pro Max 1TB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 2,
        "spec_name": "ディープブルー",
        "reduce_price": 0
    },
    {
        "goods_id": 27,
        "title": "iPhone 17 Pro Max 512GB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 0,
        "spec_name": "シルバー",
        "reduce_price": 0
    },
    {
        "goods_id": 27,
        "title": "iPhone 17 Pro Max 512GB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 1,
        "spec_name": "コズミックオレンジ",
        "reduce_price": 0
    },
    {
        "goods_id": 27,
        "title": "iPhone 17 Pro Max 512GB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 2,
        "spec_name": "ディープブルー",
        "reduce_price": 0
    },
    {
        "goods_id": 24,
        "title": "iPhone 17 Pro Max 256GB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 0,
        "spec_name": "シルバー",
        "reduce_price": 0
    },
    {
        "goods_id": 24,
        "title": "iPhone 17 Pro Max 256GB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 1,
        "spec_name": "コズミックオレンジ",
        "reduce_price": 0
    },
    {
        "goods_id": 24,
        "title": "iPhone 17 Pro Max 256GB",
        "category_three_name": "iPhone 17 Pro Max",
        "spec_index": 2,
        "spec_name": "ディープブルー",
        "reduce_price": 0
    },
    {
        "goods_id": 22,
        "title": "iPhone 17 Pro 1TB",
        "category_three_name": "iPhone 17 Pro",
        "spec_index": 0,
        "spec_name": "シルバー",
        "reduce_price": -1000
    },
    {
        "goods_id": 22,
        "title": "iPhone 17 Pro 1TB",
        "category_three_name": "iPhone 17 Pro",
        "spec_index": 1,
        "spec_name": "コズミックオレンジ",
        "reduce_price": -1000
    },
    {
        "goods_id": 22,
        "title": "iPhone 17 Pro 1TB",
        "category_three_name": "iPhone 17 Pro",
        "spec_index": 2,
        "spec_name": "ディープブルー",
        "reduce_price": -1000
    }]


def parse_device_cell(text: str):
    """
    从“機種名”单元格的多行文本中解析：
    - iphone: 机型名（第一行）
    - type: 型番
    - jan: JANコード
    """
    t = (text or "").strip()
    first_line = t.splitlines()[0].strip() if t else ""
    iphone = re.sub(r"\s*（.*?）\s*", "", first_line).strip()

    m_type = re.search(r"型番：\s*([A-Z0-9/]+)", t)
    m_jan = re.search(r"JANコード：\s*([0-9]+)", t)

    return iphone, (m_type.group(1) if m_type else None), (m_jan.group(1) if m_jan else None)


def yen_to_int(s):
    if s is None:
        return None
    m = re.search(r"([0-9,]+)\s*円", str(s))
    return int(m.group(1).replace(",", "")) if m else None


async def scrape_rank_table_to_df(headless=True) -> pd.DataFrame:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        await page.goto(URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        heading = page.locator("text=iPhone カラー別・ランク別買取価格表").first
        table = heading.locator("xpath=following::table[1]")
        await table.wait_for(state="visible", timeout=15000)

        rows = table.locator("tr")
        n = await rows.count()

        records = []
        for i in range(n):
            tr = rows.nth(i)
            tds = tr.locator("td")
            td_count = await tds.count()
            if td_count < 4:
                continue

            series = (await tds.nth(0).inner_text()).strip()
            career = (await tds.nth(1).inner_text()).strip()
            device_text = (await tds.nth(2).inner_text()).strip()

            iphone, type_code, jan = parse_device_cell(device_text)

            async def safe_td(idx):
                if td_count > idx:
                    return (await tds.nth(idx).inner_text()).strip()
                return None

            rec = {
                "シリーズ": series,
                "キャリア": career,
                "iphone": iphone,
                "type": type_code,
                "jan": jan,
                "未開封": await safe_td(3),
                "未使用": await safe_td(4),
                "ランクA": await safe_td(5),
                "ランクB": await safe_td(6),
                "ランクC": await safe_td(7),
            }
            records.append(rec)

        await browser.close()

    df = pd.DataFrame.from_records(records)

    for col in ["未開封", "未使用", "ランクA", "ランクB", "ランクC"]:
        df[col + "_int"] = df[col].apply(yen_to_int)

    return df


def _norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\u3000", " ")).strip()


def _norm_title(s: str) -> str:
    s = _norm_space(s).lower()
    s = re.sub(r"(\d+)\s*g\b", r"\1gb", s)  # 256g -> 256gb
    s = re.sub(r"(\d+)\s*gb\b", r"\1gb", s)  # 256 gb -> 256gb
    s = re.sub(r"(\d+)\s*tb\b", r"\1tb", s)  # 1 tb -> 1tb
    return s


def fetch_goodsprice_list_all(
        token: str,
        title: str = "iPhone",
        limit: int = 200,  # 尽量调大减少分页
        max_pages: int = 200,
        timeout: int = 30,
) -> dict:
    headers = {"token": token}
    merged_items = []
    page = 1
    last_page = None

    while page <= max_pages:
        params = {"page": page, "limit": limit, "title": title}
        resp = requests.get(LIST_ENDPOINT, headers=headers, params=params, timeout=timeout)
        resp.raise_for_status()
        j = resp.json()

        if j.get("code") != 1:
            raise RuntimeError(f"goodsprice/list code != 1: {j}")

        data = j.get("data", {}) or {}
        items = data.get("data", []) or []
        merged_items.extend(items)

        last_page = data.get("last_page", last_page)
        cur_page = data.get("current_page", page)

        if (last_page is not None and cur_page >= last_page) or len(items) == 0:
            out = dict(j)
            out["data"] = dict(data)
            out["data"]["data"] = merged_items
            return out

        page += 1

    raise RuntimeError("Exceeded max_pages while fetching goodsprice/list; check API paging or filters.")


def build_title_to_specs(goods_json: dict) -> dict:
    """
    title_norm -> list of specs:
      [{"spec_name", "goods_id", "spec_index"}, ...]
    """
    items = goods_json.get("data", {}).get("data", []) or []
    mp = {}
    for it in items:
        tnorm = _norm_title(it.get("title", ""))
        spec_name = _norm_space(it.get("spec_name", ""))
        if not tnorm or not spec_name:
            continue
        mp.setdefault(tnorm, []).append({
            "spec_name": spec_name,
            "goods_id": int(it["goods_id"]),
            "spec_index": int(it["spec_index"]),
        })
    return mp


def match_goods_by_iphone(iphone: str, title_to_specs: dict):
    """
    iphone: 'iPhone 17 Pro 256GB シルバー' 这样的字符串
    返回: (goods_id, spec_index) 或 (pd.NA, pd.NA)
    """
    s = _norm_space(iphone)
    if not s:
        return (pd.NA, pd.NA)

    s_norm = _norm_title(s)

    candidates = [t for t in title_to_specs.keys() if t and t in s_norm]
    if not candidates:
        # 兜底：gb/g 互换再试一次
        if "gb" in s_norm:
            alt = re.sub(r"(\d+)gb\b", r"\1g", s_norm)
        else:
            alt = re.sub(r"(\d+)g\b", r"\1gb", s_norm)
        candidates = [t for t in title_to_specs.keys() if t and t in alt]
        if not candidates:
            return (pd.NA, pd.NA)
        s_norm = alt

    best_title = max(candidates, key=len)
    specs = title_to_specs[best_title]

    hits = [sp for sp in specs if sp["spec_name"] in s]
    if not hits:
        return (pd.NA, pd.NA)

    best_spec = max(hits, key=lambda x: len(x["spec_name"]))
    return (best_spec["goods_id"], best_spec["spec_index"])


def add_goods_mapping_from_live_json(df: pd.DataFrame, goods_json: dict) -> pd.DataFrame:
    out = df.copy()
    title_to_specs = build_title_to_specs(goods_json)

    mapped = out["iphone"].apply(lambda x: match_goods_by_iphone(x, title_to_specs))
    out["goods_id"] = mapped.apply(lambda x: x[0])
    out["spec_index"] = mapped.apply(lambda x: x[1])
    return out


def build_prices_payload(df: pd.DataFrame, price_col: str) -> dict:
    required = {"goods_id", "spec_index", price_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"df missing required columns: {missing}")

    d = df[df["goods_id"].notna() & df["spec_index"].notna() & df[price_col].notna()].copy()
    d["goods_id"] = d["goods_id"].astype(int)
    d["spec_index"] = d["spec_index"].astype(int)
    d[price_col] = pd.to_numeric(d[price_col], errors="coerce")

    d = d[d[price_col].notna() & (d[price_col] > 0)]

    prices = [
        {
            "goods_id": int(r.goods_id),
            "spec_index": int(r.spec_index),
            "price": float(getattr(r, price_col)),  # API 示例是 209800.00
        }
        for r in d.itertuples(index=False)
    ]
    return {"prices": prices}


def apply_reduce_price(
        df: pd.DataFrame,
        reduce_json: list,
        base_price_col: str,
        out_price_col: str = "price_after_reduce",
        reduce_col: str = "reduce_price",
        missing_reduce_value: float = 0.0,
) -> pd.DataFrame:
    """
    在更新前，把 df 里的价格(base_price_col) 加上 reduce_json 对应的 reduce_price，
    输出到 out_price_col，并把匹配到的 reduce_price 也写回 df[reduce_col]。

    匹配键：("goods_id", "spec_index") —— 这是最稳的（不依赖 title/spec_name 字符串变化）。
    """
    required = {"goods_id", "spec_index", base_price_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"df missing required columns: {missing}")

    # reduce_json -> DataFrame
    r = pd.DataFrame(reduce_json)
    if r.empty:
        out = df.copy()
        out[reduce_col] = missing_reduce_value
        out[out_price_col] = pd.to_numeric(out[base_price_col], errors="coerce") + missing_reduce_value
        return out

    # 只保留需要的列（容错：reduce_json 结构不变，但可能带多字段）
    for col in ["goods_id", "spec_index", "reduce_price"]:
        if col not in r.columns:
            raise ValueError(f"reduce_json items missing key: {col}")

    r = r[["goods_id", "spec_index", "reduce_price"]].copy()
    r["goods_id"] = pd.to_numeric(r["goods_id"], errors="coerce").astype("Int64")
    r["spec_index"] = pd.to_numeric(r["spec_index"], errors="coerce").astype("Int64")
    r["reduce_price"] = pd.to_numeric(r["reduce_price"], errors="coerce").fillna(missing_reduce_value)

    # df 合并 reduce_price
    out = df.copy()
    out["goods_id"] = pd.to_numeric(out["goods_id"], errors="coerce").astype("Int64")
    out["spec_index"] = pd.to_numeric(out["spec_index"], errors="coerce").astype("Int64")
    out[base_price_col] = pd.to_numeric(out[base_price_col], errors="coerce")

    out = out.merge(r, on=["goods_id", "spec_index"], how="left", suffixes=("", "_r"))
    out["reduce_price"] = out["reduce_price"].fillna(missing_reduce_value)

    # 计算最终价格
    out[out_price_col] = out[base_price_col] + out["reduce_price"]

    return out


def post_update_prices(payload: dict, token: str, timeout: int = 60) -> dict:
    headers = {"token": token, "Content-Type": "application/json"}
    resp = requests.post(UPDATE_ENDPOINT, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


async def main():
    global df2
    print("=" * 20)
    print(f"  🚀 开始提取...")
    df2 = await scrape_rank_table_to_df(headless=True)
    # df2 = scrape_rank_table_to_df(headless=True)

    if df2 is None or df2.empty:
        raise RuntimeError(f" ❌ df2 is not defined or empty. Please check the scraping logic.")

    if "iphone" not in df2.columns:
        raise ValueError(f" ❌ df2 must contain column: 'iphone'")

    if PRICE_COL not in df2.columns:
        raise ValueError(f" ❌ df2 must contain column: '{PRICE_COL}'")

    print(f"  ✅ 成功提取")
    print(f"  🔍 获取映射表...")
    goods_json_live = fetch_goodsprice_list_all(token=TOKEN, title="iPhone", limit=200)
    print(f"  📝 匹配映射表...")
    df3 = add_goods_mapping_from_live_json(df2, goods_json_live)
    unmatched = df3[df3["goods_id"].isna() | df3["spec_index"].isna()][["iphone"]].drop_duplicates()
    if len(unmatched) > 0:
        print("  ⚠️ Some rows cannot be mapped to goods_id/spec_index. They will be skipped:", len(unmatched), ".")

    df3_adj = apply_reduce_price(
        df=df3,
        reduce_json=reduce_json,  # 你提供的新 json（list[dict]）
        base_price_col=PRICE_COL,  # 原始提取价格列
        out_price_col="price_to_update",  # 最终用于更新的价格列名
    )

    payload = build_prices_payload(df3_adj, price_col=PRICE_COL)
    print("  ⏳ Ready to update price entries:", len(payload["prices"]), ".")
    result = post_update_prices(payload, token=TOKEN)
    print(f"  ", "-" * 10)
    print(f"  ✅ 已完成：{result['msg']}")
    print(f"  ", "-" * 10)
    print("=" * 20)

if __name__ == "__main__":
    asyncio.run(main())