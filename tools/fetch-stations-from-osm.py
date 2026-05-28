"""
日本全国の鉄道駅データを Overpass API から取得し、
ルートリレーション・停車場リレーションから路線名・運営会社を補完して
public/data/stations.json を生成するスクリプト。

路線名の補完戦略:
  A. 駅ノードがルートリレーションのメンバーに直接含まれる場合
  B. 停車場リレーション(stop_area)経由:
     駅ノード → stop_area → 停車位置ノード(stop_position) → ルートリレーション

使い方:
  python tools/fetch-stations-from-osm.py

依存パッケージ:
  pip install requests
"""

import json
import math
import os
import re
import time
import requests

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "data", "stations.json")

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
]

# クエリ1: 駅ノード・ウェイ
STATION_QUERY = """
[out:json][timeout:900];
area["ISO3166-1"="JP"][admin_level=2]->.japan;
(
  node["railway"="station"](area.japan);
  way["railway"="station"](area.japan);
);
out center tags;
""".strip()

# クエリ2: station → stop_area → stop_positions → route の2段チェーンで取得
# (bn.stations) = 駅ノードを直接メンバーに持つリレーション (stop_area)
# (bn.sa_nodes)  = stop_area メンバーノードを直接メンバーに持つリレーション (route)
RELATION_QUERY_TMPL = """
[out:json][timeout:900];
area["ISO3166-1"="JP"][admin_level=2]->.japan;
node["railway"="station"](area.japan)->.stations;
relation["public_transport"="stop_area"](bn.stations)->.stop_areas;
node(r.stop_areas)->.sa_nodes;
(
  relation["type"="route"]["route"~"train|railway|subway|tram|monorail|light_rail|funicular"](bn.sa_nodes);
  relation["type"="route"]["route"~"train|railway|subway|tram|monorail|light_rail|funicular"](bn.stations);
  .stop_areas;
);
out body;
""".strip()

MAX_LINES = 3  # 1駅あたりの路線名最大数


def fetch_overpass(query: str, label: str) -> dict:
    for endpoint in OVERPASS_ENDPOINTS:
        print(f"  → {endpoint}", flush=True)
        try:
            resp = requests.post(
                endpoint,
                data={"data": query},
                timeout=960,
                headers={
                    "User-Agent": "nearest-station-map/1.0 (data-generation script)",
                    "Accept": "*/*",
                },
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            print("  タイムアウト。次のエンドポイントを試します...", flush=True)
        except requests.exceptions.RequestException as e:
            print(f"  エラー: {e}。次のエンドポイントを試します...", flush=True)
        time.sleep(3)
    raise RuntimeError(f"{label}: すべての Overpass エンドポイントが失敗しました。")


def clean_line_name(name: str) -> str:
    """括弧内の方向・経由表記を除去して路線名を正規化する"""
    name = re.sub(r"[\(（【\[].+?[\)）】\]]", "", name).strip()
    return re.sub(r"\s+", " ", name)


def build_route_maps(
    relation_data: dict, station_node_ids: set[int]
) -> tuple[dict[int, dict], dict[int, list[int]]]:
    """
    Returns:
      node_to_routes   : {node_id -> {"lines": [...], "operators": [...]}}
                         ルートリレーションのメンバーノードから路線情報を逆引き
      station_to_stops : {station_node_id -> [stop_position_node_id, ...]}
                         stop_area リレーション経由の停車位置マッピング
    """
    node_to_routes: dict[int, dict] = {}
    station_to_stops: dict[int, list[int]] = {}

    routes = []
    stop_areas = []

    for el in relation_data.get("elements", []):
        tags = el.get("tags", {})
        if tags.get("public_transport") == "stop_area":
            stop_areas.append(el)
        elif tags.get("type") == "route":
            routes.append(el)

    # ルートリレーション: ノードID → 路線情報
    for rel in routes:
        tags = rel.get("tags", {})
        name = (
            tags.get("name")
            or tags.get("ref:ja")
            or tags.get("ref")
        )
        if not name:
            continue
        name = clean_line_name(name)
        if not name:
            continue
        operator = (
            tags.get("operator")
            or tags.get("operator:ja")
            or tags.get("network")
            or None
        )
        for m in rel.get("members", []):
            if m.get("type") != "node":
                continue
            nid = m["ref"]
            if nid not in node_to_routes:
                node_to_routes[nid] = {"lines": [], "operators": []}
            if name not in node_to_routes[nid]["lines"]:
                node_to_routes[nid]["lines"].append(name)
            if operator and operator not in node_to_routes[nid]["operators"]:
                node_to_routes[nid]["operators"].append(operator)

    # 停車場リレーション: 駅ノード → 停車位置ノードのリスト
    for rel in stop_areas:
        node_members = [m["ref"] for m in rel.get("members", []) if m.get("type") == "node"]
        station_members = [nid for nid in node_members if nid in station_node_ids]
        stop_positions = [nid for nid in node_members if nid not in station_node_ids]
        for st_nid in station_members:
            if st_nid not in station_to_stops:
                station_to_stops[st_nid] = []
            for sp in stop_positions:
                if sp not in station_to_stops[st_nid]:
                    station_to_stops[st_nid].append(sp)

    return node_to_routes, station_to_stops


def get_route_info(
    node_id: int,
    node_to_routes: dict[int, dict],
    station_to_stops: dict[int, list[int]],
) -> dict | None:
    """
    駅ノードIDに対応する路線情報を2段階で解決する。
    A: 駅ノードがルートリレーションに直接含まれる
    B: stop_area 経由で停車位置ノードを介してルートを特定
    """
    # A: 直接メンバー
    if node_id in node_to_routes:
        return node_to_routes[node_id]

    # B: stop_area チェーン
    stop_positions = station_to_stops.get(node_id, [])
    merged: dict[str, list] = {"lines": [], "operators": []}
    for sp_id in stop_positions:
        info = node_to_routes.get(sp_id)
        if not info:
            continue
        for line in info["lines"]:
            if line not in merged["lines"]:
                merged["lines"].append(line)
        for op in info["operators"]:
            if op not in merged["operators"]:
                merged["operators"].append(op)
    return merged if (merged["lines"] or merged["operators"]) else None


def process_stations(
    station_data: dict,
    node_to_routes: dict[int, dict],
    station_to_stops: dict[int, list[int]],
) -> list[dict]:
    stations = []
    for el in station_data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        if name.startswith(":") or (name[0].isdigit() and "のりば" in name):
            continue

        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
            node_id: int | None = el["id"]
        else:
            center = el.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")
            node_id = None

        if lat is None or lon is None:
            continue

        # 駅ノードのタグから取得
        operator = tags.get("operator") or tags.get("operator:ja") or tags.get("network") or None
        line = tags.get("railway:line") or tags.get("line") or None

        # ルートリレーションで補完
        if node_id is not None:
            route_info = get_route_info(node_id, node_to_routes, station_to_stops)
            if route_info:
                if not line and route_info["lines"]:
                    line = " / ".join(route_info["lines"][:MAX_LINES])
                if not operator and route_info["operators"]:
                    operator = route_info["operators"][0]

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


def deduplicate(stations: list[dict]) -> list[dict]:
    """同名 + 座標が近い駅を統合する。情報が多い方を優先する。"""
    result = []
    THRESHOLD = 0.003  # 約300m
    for st in stations:
        merged = False
        for i, existing in enumerate(result):
            if (
                existing["name"] == st["name"]
                and abs(existing["lat"] - st["lat"]) < THRESHOLD
                and abs(existing["lon"] - st["lon"]) < THRESHOLD
            ):
                # operator/line を持つ方を優先
                if (st["operator"] or st["line"]) and not (existing["operator"] or existing["line"]):
                    result[i] = st
                merged = True
                break
        if not merged:
            result.append(st)
    return result


def main():
    print("=== 日本全国駅データ取得スクリプト (ルートリレーション補完版) ===")
    print(f"出力先: {os.path.abspath(OUTPUT_PATH)}")
    print()

    # Step 1: 駅ノード・ウェイを取得
    print("[1/2] 駅ノード・ウェイを取得中...")
    t = time.time()
    station_data = fetch_overpass(STATION_QUERY, "駅クエリ")
    n_elements = len(station_data.get("elements", []))
    print(f"  完了: {n_elements} 件 ({time.time() - t:.1f}秒)")

    # 駅ノードIDセット (stop_area マッチングに使用)
    station_node_ids: set[int] = {
        el["id"]
        for el in station_data.get("elements", [])
        if el["type"] == "node" and el.get("tags", {}).get("name")
    }

    # Step 2: 駅ノードをメンバに持つルートリレーション・停車場リレーションを逆引き
    print("\n[2/2] ルートリレーション・停車場リレーションを逆引き中...")
    print("  ※ 駅ノードを直接含むリレーションのみ取得します")
    t = time.time()
    relation_data = fetch_overpass(RELATION_QUERY_TMPL, "リレーションクエリ")
    n_rels = len(relation_data.get("elements", []))
    print(f"  完了: {n_rels} リレーション ({time.time() - t:.1f}秒)")

    # Step 3: マッピングを構築
    print("\nマッピングを構築中...")
    node_to_routes, station_to_stops = build_route_maps(relation_data, station_node_ids)
    print(f"  ルートマップ: {len(node_to_routes):,} ノード")
    print(f"  停車場マップ: {len(station_to_stops):,} 駅")

    # Step 4: 駅データを処理・補完
    print("駅データを処理・補完中...")
    stations = process_stations(station_data, node_to_routes, station_to_stops)
    print(f"  有効: {len(stations)} 件")

    # Step 5: 重複排除
    print("重複排除中...")
    stations = deduplicate(stations)

    total = len(stations)
    has_op = sum(1 for s in stations if s["operator"])
    has_line = sum(1 for s in stations if s["line"])
    has_either = sum(1 for s in stations if s["operator"] or s["line"])
    print(f"\n  総駅数:          {total}")
    print(f"  operator あり:   {has_op} ({has_op / total * 100:.1f}%)")
    print(f"  line あり:       {has_line} ({has_line / total * 100:.1f}%)")
    print(f"  どちらかあり:    {has_either} ({has_either / total * 100:.1f}%)")

    # 書き込み
    stations.sort(key=lambda s: s["name"])
    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_PATH)), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(stations, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"\n✅ 書き込み完了: {total} 駅 ({size_kb:.1f} KB)")
    print(f"   → {os.path.abspath(OUTPUT_PATH)}")


if __name__ == "__main__":
    main()
