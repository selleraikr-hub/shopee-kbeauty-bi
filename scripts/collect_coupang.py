#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
쿠팡 파트너스 Open API 기반 상품 수집 (공식 API, ToS 준수)
- COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY 환경변수(GitHub Secrets)가 없으면
  조용히 스킵하고 빈 결과를 반환한다 (키 발급 전에도 파이프라인 전체가 깨지지 않도록).
- 키 발급 후 GitHub 저장소 Settings > Secrets and variables > Actions 에 등록:
    COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY
"""
import os
import hmac
import hashlib
import json
import time
import requests
import sys

ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")

DOMAIN = "https://api-gateway.coupang.com"
SEARCH_PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"

# 수집할 키워드 (카테고리 대신 K뷰티 관련 키워드로 베스트 상품 검색)
KEYWORDS = ["스킨케어 세트", "선크림", "마스크팩", "클렌징폼", "토너 패드"]


def generate_hmac(method: str, url_path_with_query: str) -> str:
    dt = time.strftime("%y%m%d") + "T" + time.strftime("%H%M%S") + "Z"
    message = dt + method + url_path_with_query
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={dt}, signature={signature}"


def search_products(keyword: str, limit: int = 10):
    query = f"keyword={requests.utils.quote(keyword)}&limit={limit}"
    path_with_query = f"{SEARCH_PATH}?{query}"
    headers = {
        "Authorization": generate_hmac("GET", path_with_query),
        "Content-Type": "application/json",
    }
    try:
        res = requests.get(DOMAIN + path_with_query, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("data", {}).get("productData", [])
    except requests.RequestException as e:
        print(f"[WARN] 쿠팡 검색 실패 ({keyword}): {e}", file=sys.stderr)
        return []


def main():
    if not ACCESS_KEY or not SECRET_KEY:
        print("[SKIP] COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY 미설정 — 쿠팡 수집 건너뜀")
        with open("collected_coupang.json", "w", encoding="utf-8") as f:
            json.dump({"_status": "pending_api_key"}, f, ensure_ascii=False, indent=2)
        return

    result = {}
    for kw in KEYWORDS:
        items = search_products(kw)
        result[kw] = [
            {
                "rank": i + 1,
                "name": p.get("productName"),
                "price": p.get("productPrice"),
                "link": p.get("productUrl"),
                "image": p.get("productImage"),
            }
            for i, p in enumerate(items)
        ]
        print(f"[INFO] {kw}: {len(items)}건")
        time.sleep(1)

    with open("collected_coupang.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("[DONE] 쿠팡 수집 완료")


if __name__ == "__main__":
    main()
