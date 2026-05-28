#!/usr/bin/env python3
"""
国土数値情報 N05（鉄道時系列データ）の ShapeFile から
アプリ用の stations.json を生成するスクリプト。

前提ライブラリ:
    pip install geopandas pyproj shapely

使い方:
    python tools/generate-stations.py

入力:
    data-source/N05/Station2.shp

出力:
    public/data/stations.json
"""

import json
import math
import os
import sys
import warnings
from pathlib import Path

try:
    import geopandas as gpd
except ImportError:
    print("[ERROR] geopandas が見つかりません。以下を実行してください:")
    print("  pip install geopandas pyproj shapely")
    sys.exit(1)

# ─── パス設定 ────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
INPUT_SHP = ROOT_DIR / "data-source" / "N05" / "Station2.shp"
OUTPUT_JSON = ROOT_DIR / "public" / "data" / "stations.json"

# ─── N05 属性のカラム名マッピング候補 ────────────────────────
# 年度や形式でカラム名が変わるため、候補を列挙して最初に見つかったものを使う
COLUMN_CANDIDATES = {
    "station_name": [
        "N05_011",  # 駅名（時系列）
        "N05_003",  # 駅名（従来）
        "StationNam",
        "station_name",
        "NAME",
    ],
    "operator": [
        "N05_003",  # 運営会社（時系列）
        "N05_009",
        "OperatorNa",
        "operator",
        "OPERATOR",
    ],
    "line_name": [
        "N05_002",  # 路線名
        "RailwayNam",
        "line_name",
        "LINE",
    ],
    "close_year": [
        "N05_005b",  # 設置終了年（9999 = 現存）
        "N05_007",
        "CloseYear",
        "close_year",
    ],
}

CLOSE_YEAR_ACTIVE = "9999"  # この値なら現存駅
COORD_THRESHOLD = 0.003     # 重複判定の座標差閾値（約 300m）
MAX_LINES = 5               # 1駅にまとめる路線数の上限


def find_column(gdf_columns: list[str], candidates: list[str]) -> str | None:
    """候補リストから実際に存在するカラム名を返す。"""
    for c in candidates:
        if c in gdf_columns:
            return c
    return None


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    p = math.pi / 180
    a = (
        math.sin((lat2 - lat1) * p / 2) ** 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def deduplicate(stations: list[dict]) -> list[dict]:
    """
    同名かつ座標差が閾値以内の駅を 1 件にまとめる。
    路線名・運営会社は結合して保持する。
    """
    result: list[dict] = []

    for st in stations:
        matched = None
        for r in result:
            if (
                r["name"] == st["name"]
                and abs(r["lat"] - st["lat"]) < COORD_THRESHOLD
                and abs(r["lon"] - st["lon"]) < COORD_THRESHOLD
            ):
                matched = r
                break

        if matched:
            # 路線名を追記（重複なし）
            if st.get("line") and st["line"] not in matched["line"].split("、"):
                lines = matched["line"].split("、") if matched["line"] else []
                if len(lines) < MAX_LINES:
                    lines.append(st["line"])
                    matched["line"] = "、".join(lines)
            # 運営会社を追記（重複なし）
            if st.get("operator") and st["operator"] not in matched.get("operator", ""):
                ops = matched["operator"].split("、") if matched.get("operator") else []
                if len(ops) < MAX_LINES:
                    ops.append(st["operator"])
                    matched["operator"] = "、".join(ops)
        else:
            result.append(dict(st))

    return result


def main() -> None:
    print(f"[INFO] 入力ファイル: {INPUT_SHP}")
    print(f"[INFO] 出力ファイル: {OUTPUT_JSON}")

    if not INPUT_SHP.exists():
        print(f"[ERROR] 入力ファイルが見つかりません: {INPUT_SHP}")
        print()
        print("国土数値情報 N05（鉄道時系列データ）の ShapeFile を以下に配置してください:")
        print(f"  {INPUT_SHP}")
        print()
        print("ダウンロード先:")
        print("  https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-v3_1.html")
        sys.exit(1)

    # ─── ShapeFile 読み込み ─────────────────────────────────
    print("[INFO] ShapeFile を読み込んでいます...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gdf = gpd.read_file(INPUT_SHP, encoding="utf-8")

    # エンコードが utf-8 で読めなければ cp932 で再試行
    if gdf.empty or all(gdf.columns.str.startswith("N05_") is False):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gdf = gpd.read_file(INPUT_SHP, encoding="cp932")
        except Exception:
            pass

    print(f"[INFO] 読み込み件数: {len(gdf)}")
    print(f"[INFO] カラム一覧: {list(gdf.columns)}")
    print(f"[INFO] CRS: {gdf.crs}")

    # ─── 座標系を WGS84 (EPSG:4326) に変換 ────────────────────
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        print("[INFO] 座標系を WGS84 に変換しています...")
        gdf = gdf.to_crs(epsg=4326)

    # ─── カラムマッピング ────────────────────────────────────
    cols = list(gdf.columns)
    col_name     = find_column(cols, COLUMN_CANDIDATES["station_name"])
    col_operator = find_column(cols, COLUMN_CANDIDATES["operator"])
    col_line     = find_column(cols, COLUMN_CANDIDATES["line_name"])
    col_close    = find_column(cols, COLUMN_CANDIDATES["close_year"])

    print(f"[INFO] 駅名カラム    : {col_name}")
    print(f"[INFO] 運営会社カラム: {col_operator}")
    print(f"[INFO] 路線名カラム  : {col_line}")
    print(f"[INFO] 設置終了年カラム: {col_close}")

    if col_name is None:
        print("[ERROR] 駅名カラムが見つかりませんでした。COLUMN_CANDIDATES を確認してください。")
        sys.exit(1)

    if col_close is None:
        print("[WARNING] 設置終了年カラムが見つかりません。廃止駅を含む全データを出力します。")

    # ─── 現存駅フィルタ ─────────────────────────────────────
    if col_close:
        before = len(gdf)
        gdf = gdf[gdf[col_close].astype(str) == CLOSE_YEAR_ACTIVE]
        print(f"[INFO] 現存駅フィルタ: {before} → {len(gdf)} 件")

    # ─── ジオメトリから緯度経度を取得 ─────────────────────────
    print("[INFO] 座標を抽出しています...")
    stations_raw: list[dict] = []
    skipped = 0

    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            skipped += 1
            continue

        # Point の場合はそのまま、LineString/Polygon はセントロイドを使用
        if geom.geom_type == "Point":
            lon, lat = geom.x, geom.y
        else:
            centroid = geom.centroid
            lon, lat = centroid.x, centroid.y

        name = str(row[col_name]).strip() if col_name and row[col_name] else ""
        if not name or name in ("nan", "None", ""):
            skipped += 1
            continue

        operator = str(row[col_operator]).strip() if col_operator and row[col_operator] else ""
        line     = str(row[col_line]).strip()     if col_line and row[col_line]     else ""

        operator = "" if operator in ("nan", "None") else operator
        line     = "" if line     in ("nan", "None") else line

        stations_raw.append({
            "id": f"n05-{str(idx).zfill(6)}",
            "name": name,
            "lat": round(lat, 7),
            "lon": round(lon, 7),
            "operator": operator,
            "line": line,
            "source": "国土数値情報 鉄道時系列データ",
        })

    print(f"[INFO] 座標抽出: {len(stations_raw)} 件（スキップ: {skipped} 件）")

    # ─── 重複排除 ────────────────────────────────────────────
    stations_dedup = deduplicate(stations_raw)
    print(f"[INFO] 重複排除後: {len(stations_dedup)} 件")

    # ─── 空文字フィールドを None に変換 ─────────────────────
    for st in stations_dedup:
        if not st.get("operator"):
            st["operator"] = None
        if not st.get("line"):
            st["line"] = None

    # ─── 出力 ───────────────────────────────────────────────
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(stations_dedup, f, ensure_ascii=False, indent=2)

    size_kb = OUTPUT_JSON.stat().st_size / 1024
    print(f"[INFO] 出力完了: {OUTPUT_JSON} ({size_kb:.1f} KB)")
    print(f"[INFO] 駅数: {len(stations_dedup)} 件")


if __name__ == "__main__":
    main()
