#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
올리브영 카테고리별 베스트 상품 자동 수집
- 공개 베스트 목록 페이지(getBestList.do)를 조회, 1일 1회(카테고리당 1회) 요청만 보냄
- 참고: 이 엔드포인트는 로그인/CAPTCHA 없이 열람 가능한 공개 랭킹 페이지지만,
  올리브영 robots.txt는 자동 접근을 허용하지 않으므로 저빈도(1일 1회) 사용을 전제로 함.
- HTML 구조가 바뀌면 파싱이 깨질 수 있음 → 실패 시 해당 카테고리는 건너뛰고 로그만 남김
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import sys

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Referer": "https://www.oliveyoung.co.kr/store/main/main.do",
}

# 카테고리명 -> fltDispCatNo 하위 코드 (필요 시 카테고리 추가/삭제)
CATEGORIES = {
    "스킨케어": "100000010001",
    "마스크팩": "100000010009",
    "클렌징": "100000010010",
    "선케어": "100000010011",
    "더모코스메틱": "100000010008",
    "헤어케어": "100000010004",
    "바디케어": "100000010003",
}

BASE_URL = "https://www.oliveyoung.co.kr/store/main/getBestList.do"
FIXED_DISP_CAT_NO = "900000100100001"  # 베스트 전체 랭킹 진입 카테고리(고정)


def fetch_category(cat_name: str, flt_disp_cat_no: str, limit: int = 10):
    """카테고리 하나의 베스트 TOP N을 가져온다. 실패 시 빈 리스트 반환."""
    params = {"dispCatNo": FIXED_DISP_CAT_NO, "fltDispCatNo": flt_disp_cat_no}
    try:
        res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        print(f"[WARN] {cat_name} 요청 실패: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    items = []

    # NOTE: 아래 셀렉터는 공개된 마크업 패턴 기준 1차 추정치입니다.
    # 실제 실행(Actions 로그)에서 0건이 나오면, 그 시점의 실제 HTML을 보고
    # li.prd_info / .prd_name / .tx_num 등 클래스명을 갱신해야 합니다.
    rows = soup.select("ul.cate_prd_list > li") or soup.select("li.flag.prd_info")

    for idx, row in enumerate(rows[:limit], start=1):
        try:
            name_tag = row.select_one(".tx_name, .prd_name")
            brand_tag = row.select_one(".tx_brand, .prd_brand")
            price_tag = row.select_one(".tx_cur .tx_num, .price .tx_num")
            link_tag = row.select_one("a")

            name = name_tag.get_text(strip=True) if name_tag else None
            brand = brand_tag.get_text(strip=True) if brand_tag else None
            price_raw = price_tag.get_text(strip=True) if price_tag else None
            price = int(price_raw.replace(",", "")) if price_raw and price_raw.replace(",", "").isdigit() else None
            link = link_tag["href"] if link_tag and link_tag.has_attr("href") else None
            if link and link.startswith("/"):
                link = "https://www.oliveyoung.co.kr" + link

            if name:
                items.append({
                    "rank": idx,
                    "brand": brand,
                    "name": name,
                    "price": price,
                    "link": link,
                })
        except Exception as e:
            print(f"[WARN] {cat_name} 항목 파싱 실패: {e}", file=sys.stderr)
            continue

    return items


def main():
    result = {}
    for cat_name, cat_code in CATEGORIES.items():
        print(f"[INFO] 수집 중: {cat_name}")
        items = fetch_category(cat_name, cat_code)
        result[cat_name] = items
        print(f"[INFO] {cat_name}: {len(items)}건 수집")
        time.sleep(2)  # 카테고리 간 최소 텀 (서버 부담 최소화)

    with open("collected_oliveyoung.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in result.values())
    print(f"[DONE] 올리브영 총 {total}건 수집 완료")
    if total == 0:
        print("[ALERT] 0건 수집 — 셀렉터가 깨졌을 가능성이 높습니다. HTML 구조 재확인 필요", file=sys.stderr)


if __name__ == "__main__":
    main()
