import requests, json, os, io, csv
from datetime import datetime

def fetch_list():
    url = "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=RESULT_0000000000001789&fileDetailSn=1"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=30)
        print("status: " + str(res.status_code))
        content = res.content.decode("cp949", errors="replace")
        reader = csv.DictReader(io.StringIO(content))
        result = []
        today = datetime.now()
        today_str = today.strftime("%Y%m%d")
        for row in reader:
            rb = row.get("청약접수시작일", "").replace("-","").replace(".","")
            re = row.get("청약접수종료일", "").replace("-","").replace(".","")
            result.append({
                "id": row.get("주택관리번호", ""),
                "name": row.get("주택명", ""),
                "location": row.get("공급위치", ""),
                "region": row.get("공급지역명", ""),
                "supplyCount": row.get("공급규모", ""),
                "recruitDate": rb,
                "recruitEndDate": re,
                "winnerDate": row.get("당첨자발표일", ""),
                "moveInDate": row.get("입주예정월", ""),
                "constructor": row.get("건설업체명(시공사)", ""),
                "status": "진행중" if rb <= today_str <= re else "예정",
                "type59": None,
                "type84": None,
            })
        print("파싱된 행: " + str(len(result)) + "건")
        return result
    except Exception as e:
        print("오류: " + str(e))
        return []

def fetch_detail_csv():
    url = "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=RESULT_0000000000001790&fileDetailSn=1"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=30)
        content = res.content.decode("cp949", errors="replace")
        reader = csv.DictReader(io.StringIO(content))
        details = {}
        for row in reader:
            mid = row.get("주택관리번호", "")
            if mid not in details:
                details[mid] = []
            lottery = row.get("추첨제세대수", "0") or "0"
            supply = row.get("일반공급세대수", "1") or "1"
            price = row.get("분양최고금액", "0") or "0"
            try: lr = round(int(lottery) / max(int(supply), 1) * 100)
            except: lr = 0
            try: p = int(price)
            except: p = 0
            details[mid].append({
                "area": row.get("주택형", ""),
                "supplyCount": supply,
                "lotteryCount": lottery,
                "supplyPrice": p,
                "lotteryRatio": lr,
            })
        return details
    except Exception as e:
        print("상세 오류: " + str(e))
        return {}

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    try:
        nearby = json.load(open("nearby_prices.json", encoding="utf-8"))
    except:
        nearby = {}

    print("수집 시작...")
    apts = fetch_list()
    print("공고: " + str(len(apts)) + "건")

    details = fetch_detail_csv()
    print("상세: " + str(len(details)) + "건")

    dataset = []
    for apt in apts:
        mid = apt["id"]
        types = details.get(mid, [])
        if not any(int(t.get("lotteryCount","0") or "0") > 0 for t in types):
            continue
        apt["type59"] = next((t for t in types if "59" in str(t.get("area",""))), None)
        apt["type84"] = next((t for t in types if "84" in str(t.get("area",""))), None)
        dataset.append(apt)

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
