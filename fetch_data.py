import requests, json, os, re
from datetime import datetime

def fetch_list():
    result = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for page in range(1, 4):
        url = "https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancListView.do?pageIndex=" + str(page)
        try:
            res = requests.get(url, headers=headers, timeout=20)
            html = res.text
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            for row in rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cells) < 8:
                    continue
                def clean(s):
                    return re.sub(r'<[^>]+>', '', s).strip()
                region = clean(cells[0])
                name_match = re.search(r'<a[^>]*>([^<]+)</a>', cells[3])
                name = name_match.group(1).strip() if name_match else clean(cells[3])
                name = name.replace("NEW", "").strip()
                constructor = clean(cells[4])
                announce_date = clean(cells[6])
                period = clean(cells[7])
                winner_date = clean(cells[8]) if len(cells) > 8 else ""
                dates = re.findall(r'\d{4}-\d{2}-\d{2}', period)
                rb = dates[0].replace("-","") if len(dates) > 0 else ""
                re_ = dates[1].replace("-","") if len(dates) > 1 else ""
                today_str = datetime.now().strftime("%Y%m%d")
                if not name or not region:
                    continue
                result.append({
                    "id": name + "_" + rb,
                    "name": name,
                    "location": "",
                    "region": region,
                    "supplyCount": "",
                    "recruitDate": rb,
                    "recruitEndDate": re_,
                    "winnerDate": winner_date.replace("-",""),
                    "moveInDate": "",
                    "constructor": constructor,
                    "status": "진행중" if rb <= today_str <= re_ else "예정",
                    "type59": None,
                    "type84": None,
                })
        except Exception as e:
            print("page " + str(page) + " 오류: " + str(e))
    return result

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    try:
        nearby = json.load(open("nearby_prices.json", encoding="utf-8"))
    except:
        nearby = {}

    print("수집 시작...")
    apts = fetch_list()
    print("공고: " + str(len(apts)) + "건")

    updated = datetime.now().strftime("%Y.%m.%d %H:%M")
    cjs = json.dumps(apts, ensure_ascii=False)
    njs = json.dumps(nearby, ensure_ascii=False)

    json.dump(apts, open("docs/data.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)

    try:
        html = open("template.html", encoding="utf-8").read()
    except:
        html = "<html><body><h1>template.html 없음</h1></body></html>"

    html = html.replace("UPDATED_AT", updated).replace("CARDS_DATA", cjs).replace("NEARBY_DATA", njs)
    open("docs/index.html","w",encoding="utf-8").write(html)
    print("완료! " + str(len(apts)) + "개 단지")
