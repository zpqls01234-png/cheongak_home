import requests, json, os
from datetime import datetime, timedelta

API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
BASE_URL = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1"

def fetch_list():
    today = datetime.now()
    try:
        res = requests.get(BASE_URL + "/getAPTLttotPblancDetail", params={
            "serviceKey": API_KEY,
            "page": "1",
            "perPage": "100",
        }, timeout=20)
        print("status: " + str(res.status_code))
        print("response: " + res.text[:300])
        if res.status_code != 200:
            return []
        data = res.json()
        items = data.get("data", [])
        result = []
        today_str = today.strftime("%Y%m%d")
        for item in items:
            rb = str(item.get("RCEPT_BGNDE", "")).replace("-","")
            re = str(item.get("RCEPT_ENDDE", "")).replace("-","")
            result.append({
                "id": str(item.get("HOUSE_MANAGE_NO", "")),
                "name": item.get("HOUSE_NM", ""),
                "location": item.get("HSSPLY_ADRES", ""),
                "region": item.get("SUBSCRPT_AREA_CODE_NM", ""),
                "supplyCount": str(item.get("TOT_SUPLY_HSHLDCO", "")),
                "recruitDate": rb,
                "recruitEndDate": re,
                "winnerDate": str(item.get("PRZWNER_PRESNATN_DE", "")),
                "moveInDate": str(item.get("MOVE_IN_YM", "")),
                "constructor": item.get("BSNS_MBY_NM", ""),
                "status": "진행중" if rb <= today_str <= re else "예정",
                "type59": None, "type84": None,
            })
        return result
    except Exception as e:
        print("fetch_list 오류: " + str(e))
        return []

def fetch_detail(manage_no):
    try:
        res = requests.get(BASE_URL + "/getAPTLttotPblancMdl", params={
            "serviceKey": API_KEY,
            "page": "1",
            "perPage": "50",
            "cond[HOUSE_MANAGE_NO::EQ]": manage_no,
        }, timeout=20)
        if res.status_code != 200:
            return []
        data = res.json()
        items = data.get("data", [])
        types = []
        for item in items:
            lottery = str(item.get("CHCSR_HSHLDCO", "0") or "0")
            supply = str(item.get("SUPLY_HSHLDCO", "1") or "1")
            price_str = str(item.get("LTTOT_TOP_AMOUNT", "") or "")
            try: lr = round(int(lottery) / max(int(supply), 1) * 100)
            except: lr = 0
            try: price = int(price_str) * 10000 if price_str else 0
            except: price = 0
            types.append({
                "area": str(item.get("SUPLY_AR", "")),
                "supplyCount": supply,
                "lotteryCount": lottery,
                "supplyPrice": price,
                "lotteryRatio": lr,
            })
        return types
    except Exception as e:
        print("fetch_detail 오류: " + str(e))
        return []

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    try:
        nearby = json.load(open("nearby_prices.json", encoding="utf-8"))
    except:
        nearby = {}

    print("수집 시작...")
    apts = fetch_list()
    print("공고: " + str(len(apts)) + "건")

    dataset = []
    for apt in apts:
        try:
            types = fetch_detail(apt["id"])
            if not any(int(t.get("lotteryCount","0") or "0") > 0 for t in types):
                continue
            apt["type59"] = next((t for t in types if "59" in str(t.get("area",""))), None)
            apt["type84"] = next((t for t in types if "84" in str(t.get("area",""))), None)
            dataset.append(apt)
        except Exception as e:
            print("처리 오류: " + str(e))

    print("추첨물량 단지: " + str(len(dataset)) + "건")
    json.dump(dataset, open("docs/data.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)

    updated = datetime.now().strftime("%Y.%m.%d %H:%M")
    cjs = json.dumps(dataset, ensure_ascii=False)
    njs = json.dumps(nearby, ensure_ascii=False)

    try:
        html = open("template.html", encoding="utf-8").read()
    except:
        html = "<html><body><h1>template.html 없음</h1></body></html>"

    html = html.replace("UPDATED_AT", updated).replace("CARDS_DATA", cjs).replace("NEARBY_DATA", njs)
    open("docs/index.html","w",encoding="utf-8").write(html)
    print("완료! " + str(len(dataset)) + "개 단지")
