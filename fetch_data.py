import requests, json, os, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
BASE_URL = "http://apis.data.go.kr/B552555/APTLttotPblancDetail"

def g(item, tag):
    el = item.find(tag)
    return (el.text or "").strip() if el is not None else ""

def fetch_list():
    today = datetime.now()
    res = requests.get(BASE_URL + "/getLttotPblancList", params={
        "serviceKey": API_KEY,
        "startMonth": (today - timedelta(days=30)).strftime("%Y%m"),
        "endMonth": today.strftime("%Y%m"),
        "numOfRows": "100", "pageNo": "1"
    }, timeout=20)
    print("list status:", res.status_code)
    root = ET.fromstring(res.content)
    result = []
    for item in root.findall(".//item"):
        rb = g(item, "RCEPT_BGNDE")
        re = g(item, "RCEPT_ENDDE")
        ts = today.strftime("%Y%m%d")
        result.append({
            "id": g(item, "HOUSE_MANAGE_NO"),
            "name": g(item, "HOUSE_NM"),
            "location": g(item, "HSSPLY_ADRES"),
            "region": g(item, "SUBSCRPT_AREA_CODE_NM"),
            "supplyCount": g(item, "TOT_SUPLY_HSHLDCO"),
            "recruitDate": rb, "recruitEndDate": re,
            "winnerDate": g(item, "PRZWNER_PRESNATN_DE"),
            "moveInDate": g(item, "MOVE_IN_YM"),
            "constructor": g(item, "BSNS_MBY_NM"),
            "status": "진행중" if rb <= ts <= re else "예정",
            "type59": None, "type84": None,
        })
    return result

def fetch_detail(manage_no):
    res = requests.get(BASE_URL + "/getLttotPblancDetail", params={
        "serviceKey": API_KEY, "houseManageNo": manage_no,
        "numOfRows": "50", "pageNo": "1"
    }, timeout=20)
    root = ET.fromstring(res.content)
    types = []
    for item in root.findall(".//item"):
        lottery = g(item, "CHCSR_HSHLDCO") or "0"
        supply = g(item, "SUPLY_HSHLDCO") or "1"
        price_str = g(item, "LTTOT_TOP_AMOUNT")
        try: lr = round(int(lottery) / max(int(supply), 1) * 100)
        except: lr = 0
        try: price = int(price_str) * 10000 if price_str else 0
        except: price = 0
        types.append({
            "area": g(item, "SUPLY_AR"),
            "supplyCount": supply,
            "lotteryCount": lottery,
            "supplyPrice": price,
            "lotteryRatio": lr,
        })
    return types

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    try:
        nearby = json.load(open("nearby_prices.json", encoding="utf-8"))
    except:
        nearby = {}

    print("수집 시작...")
    apts = fetch_list()
    print("공고:", len(apts), "건")

    dataset = []
    for apt in apts:
        types = fetch_detail(apt["id"])
        if not any(int(t.get("lotteryCount","0") or "0") > 0 for t in types):
            continue
        apt["type59"] = next((t for t in types if "59" in str(t.get("area",""))), None)
        apt["type84"] = next((t for t in types if "84" in str(t.get("area",""))), None)
        dataset.append(apt)
    print("추첨물량 단지:", len(dataset), "건")

    json.dump(dataset, open("docs/data.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)

    updated = datetime.now().strftime("%Y.%m.%d %H:%M")
    cjs = json.dumps(dataset, ensure_ascii=False)
    njs = json.dumps(nearby, ensure_ascii=False)

    html = open("template.html", encoding="utf-8").read()
    html = html.replace("UPDATED_AT", updated).replace("CARDS_DATA", cjs).replace("NEARBY_DATA", njs)
    open("docs/index.html","w",encoding="utf-8").write(html)
    print("완료!", len(dataset), "개 단지")
