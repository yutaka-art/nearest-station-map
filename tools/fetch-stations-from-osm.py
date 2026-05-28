"""
日本全国の鉄道駅データを Overpass API から取得し、
public/data/stations.json を生成するスクリプト。

使い方:
  python tools/fetch-stations-from-osm.py

依存パッケージ:
  pip install requests
"""

import json
import math
import os
import sys
import time
import requests

# 出力先
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "data", "stations.json")

# Overpass API エンドポイント (複数用意してフォールバック)
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
]

QUERY = """
[out:json][timeout:900];
area["ISO3166-1"="JP"][admin_level=2]->.japan;
(
  node["railway"="station"](area.japan);
  way["railway"="station"](area.japan);
);
out center tags;
""".strip()


def build_query() -> str:
    return QUERY


def fetch_overpass(query: str) -> dict:
    for endpoint in OVERPASS_ENDPOINTS:
        print(f"  → {endpoint}", flush=True)
        try:
            resp = requests.post(
                endpoint,
                data={"data": query},
                timeout=960,
                headers={"User-Agent": "nearest-station-map/1.0 (data-generation script)"},
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            print("  タイムアウト。次のエンドポイントを試します...", flush=True)
        except requests.exceptions.RequestException as e:
            print(f"  エラー: {e}。次のエンドポイントを試します...", flush=True)
        time.sleep(3)
    raise RuntimeError("すべての Overpass エンドポイントが失敗しました。")


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def deduplicate(stations: list[dict]) -> list[dict]:
    """同名 + 座標が近い駅を統合する (同一駅の別エントリを除去)"""
    result = []
    THRESHOLD = 0.003  # 約300m
    for st in stations:
        is_dup = False
        for existing in result:
            if (
                existing["name"] == st["name"]
                and abs(existing["lat"] - st["lat"]) < THRESHOLD
                and abs(existing["lon"] - st["lon"]) < THRESHOLD
            ):
                is_dup = True
                break
        if not is_dup:
            result.append(st)
    return result


def process_elements(elements: list) -> list[dict]:
    stations = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        # 日本語名のみ対象 (名前が ASCII のみの場合はスキップしない — 外国語の駅名もありうる)
        # lat/lon の取得 (node は直接、way は center を使う)
        if el["type"] == "node":
            lat = el.get("lat")
            lon = el.get("lon")
        else:
            center = el.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")

        if lat is None or lon is None:
            continue

        # 明らかな非駅名をスキップ (数字始まり の「○階のりば」等、先頭コロン等)
        if name.startswith(":") or (name[0].isdigit() and "のりば" in name):
            continue

        operator = tags.get("operator") or tags.get("network") or None
        line = tags.get("railway:line") or tags.get("line") or None

        stations.append({
            "id": f"{el['type']}/{el['id']}",
            "name": name,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "operator": operator,
            "line": line,
            "source": "osm",
        })

    return stations


def main():
    print("=== 日本全国駅データ取得スクリプト (Overpass API) ===")
    print(f"出力先: {os.path.abspath(OUTPUT_PATH)}")
    print()

    query = build_query()
    print("Overpass API にクエリを送信中...(数分かかることがあります)")
    start = time.time()

    data = fetch_overpass(query)

    elapsed = time.time() - start
    elements = data.get("elements", [])
    print(f"取得完了: {len(elements)} 件 ({elapsed:.1f}秒)")

    print("データを処理中...")
    stations = process_elements(elements)
    print(f"有効な駅: {len(stations)} 件")

    print("重複排除中...")
    stations = deduplicate(stations)
    print(f"重複排除後: {len(stations)} 件")

    # 駅名でソート
    stations.sort(key=lambda s: s["name"])

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(stations, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"\n✅ 書き込み完了: {len(stations)} 駅 ({size_kb:.1f} KB)")
    print(f"   → {os.path.abspath(OUTPUT_PATH)}")


if __name__ == "__main__":
    main()
