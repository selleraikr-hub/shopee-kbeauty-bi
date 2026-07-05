#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collected_*.json 결과들을 data.json의 autoCollected 섹션에 병합.
기존 data.json의 다른 키(oliveYoungTop10 등 레거시)는 건드리지 않음.
"""
import json
import os
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
DATA_PATH = "data.json"


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def main():
    data = load_json(DATA_PATH, {})

    oliveyoung = load_json("collected_oliveyoung.json", {})
    coupang = load_json("collected_coupang.json", {"_status": "pending_api_key"})

    data["autoCollected"] = {
        "collectedAt": datetime.now(KST).isoformat(),
        "oliveyoung": oliveyoung,
        "coupang": coupang,
        "daiso": {"_status": "not_implemented_js_rendered_site"},
    }

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[DONE] data.json 갱신 완료 ({DATA_PATH})")


if __name__ == "__main__":
    main()
