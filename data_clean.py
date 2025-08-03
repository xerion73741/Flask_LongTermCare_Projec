import pandas as pd
import re
from collections import defaultdict

# --- 資料讀取與清洗 ---
def build_city_district_map():
    df = pd.read_csv("adrees.csv", encoding="utf-8")
    pattern = re.compile(r"(.+?[市縣])(.+?[區鄉鎮])")
    city_map = defaultdict(set)

    for address in df["地址全址"].dropna():
        match = pattern.match(address)
        if match:
            city, district = match.groups()
            if district.endswith(("區", "鎮", "鄉")):
                city_map[city].add(district)

    # 轉成排序好的 list
    return {city: sorted(districts) for city, districts in city_map.items()}

city_district_data = build_city_district_map()