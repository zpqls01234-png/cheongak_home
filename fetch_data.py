"""
청약홈 데이터 자동 수집 스크립트
공공데이터포털 한국부동산원 청약정보 API 사용
매일 GitHub Actions에서 실행됨
"""
import requests
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from urllib.parse import quote

API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "http://apis.data.go.kr/B552555/APTLttotPblancDetail"

def fetch_apt_list():
    """아파트 분양 공고 목록 조회 (최근 30일)"""
    today = datetime.now()
    start = (today - timedelta(days=30)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")

    url = f"{BASE_URL}/getLttotPblancList"
    params = {
        "serviceKey": API_KEY,
        "startMonth": today.strftime("%Y%m"),
        "endMonth": today.strftime("%Y%m"),
        "numOfRows": 100,
        "pageNo": 1,
    }

    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        root = ET.fromstring(res.content)
        items = root.findall(".//item")
        result = []
        for item in items:
            get = lambda tag: (item.find(tag).text or "").strip() if item.find(tag) is not None else ""
            result.append({
                "id": get("HOUSE_MANAGE_NO"),
                "name": get("HOUSE_NM"),
                "location": f"{get('SUBSCRPT_AREA_CODE_NM')} {get('HSSPLY_ADRES')}",
                "region": get("SUBSCRPT_AREA_CODE_NM"),
                "supplyCount": get("TOT_SUPLY_HSHLDCO"),
                "recruitDate": get("RCEPT_BGNDE"),
                "recruitEndDate": get("RCEPT_ENDDE"),
                "winnerDate": get("PRZWNER_PRESNATN_DE"),
                "moveInDate": get("MOVE_IN_YM"),
                "constructor": get("BSNS_MBY_NM"),
                "houseType": get("HOUSE_SECD_NM"),
                "status": "진행중" if get("RCEPT_BGNDE") <= today.strftime("%Y%m%d") <= get("RCEPT_ENDDE") else "예정",
            })
        return result
    except Exception as e:
        print(f"[ERROR] 목록 조회 실패: {e}")
        return []

def fetch_apt_detail(manage_no):
    """단지별 타입/분양가 상세 조회"""
    url = f"{BASE_URL}/getLttotPblancDetail"
    params = {
        "serviceKey": API_KEY,
        "houseManageNo": manage_no,
        "numOfRows": 50,
        "pageNo": 1,
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        root = ET.fromstring(res.content)
        items = root.findall(".//item")
        types = []
        for item in items:
            get = lambda tag: (item.find(tag).text or "").strip() if item.find(tag) is not None else ""
            area_str = get("SUPLY_AR")
            supply_price = get("LTTOT_TOP_AMOUNT")
            lottery_count = get("CHCSR_HSHLDCO")
            gajeom_count = get("GAGYM_HSHLDCO")

            try:
                area = float(area_str)
                price = int(supply_price) * 10000 if supply_price else 0  # 만원 단위
            except:
                area = 0
                price = 0

            types.append({
                "type": get("HOUSE_TY"),
                "area": area_str,
                "supplyCount": get("SUPLY_HSHLDCO"),
                "lotteryCount": lottery_count,  # 추첨제 세대수
                "gajeomCount": gajeom_count,   # 가점제 세대수
                "supplyPrice": price,
                "lotteryRatio": round(int(lottery_count or 0) / max(int(get("SUPLY_HSHLDCO") or 1), 1) * 100) if lottery_count else 0,
            })
        return types
    except Exception as e:
        print(f"[ERROR] 상세 조회 실패 ({manage_no}): {e}")
        return []

def calc_margin(supply_price, nearby_price):
    if not supply_price or supply_price == 0:
        return 0, 0
    diff = nearby_price - supply_price
    pct = round((diff / supply_price) * 100)
    return diff, pct

def build_dataset():
    """전체 데이터셋 빌드"""
    print(f"[{datetime.now()}] 청약 데이터 수집 시작...")
    apts = fetch_apt_list()
    print(f"  → 공고 {len(apts)}건 수집")

    dataset = []
    for apt in apts:
        types = fetch_apt_detail(apt["id"])
        # 59㎡, 84㎡ 타입만 추출
        t59 = next((t for t in types if "59" in str(t.get("area",""))), None)
        t84 = next((t for t in types if "84" in str(t.get("area",""))), None)

        # 추첨 물량 있는 단지만 포함 (1주택자 대상)
        has_lottery = any(int(t.get("lotteryCount") or 0) > 0 for t in types)
        if not has_lottery:
            continue

        # 기본 주변시세는 수동 세팅값 유지 (API로 시세 못 가져옴)
        apt["types"] = types
        apt["type59"] = t59
        apt["type84"] = t84
        dataset.append(apt)

    print(f"  → 1주택자 추첨물량 있는 단지: {len(dataset)}건")
    return dataset

def fmt_price(p):
    if not p:
        return "-"
    p = int(p)
    if p >= 10000:
        u = p // 10000
        m = p % 10000
        return f"{u}억 {m:,}만" if m else f"{u}억"
    return f"{p:,}만"

def generate_html(dataset, manual_nearby):
    """HTML 파일 생성"""

    cards_js = json.dumps(dataset, ensure_ascii=False, indent=2)
    nearby_js = json.dumps(manual_nearby, ensure_ascii=False, indent=2)
    updated = datetime.now().strftime("%Y.%m.%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>1주택자 청약 안전마진 대시보드</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#080c12;color:#dde4f0;font-family:'Noto Sans KR','Apple SD Gothic Neo',sans-serif;min-height:100vh}}
  .bg-grid{{position:fixed;inset:0;opacity:.03;pointer-events:none;z-index:0;background-image:linear-gradient(rgba(0,255,135,1) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,135,1) 1px,transparent 1px);background-size:48px 48px}}
  .bg-glow{{position:fixed;top:-120px;right:-120px;width:450px;height:450px;background:radial-gradient(circle,rgba(0,255,135,.06) 0%,transparent 70%);border-radius:50%;pointer-events:none;z-index:0}}
  .wrap{{position:relative;z-index:1;max-width:1080px;margin:0 auto;padding:28px 16px}}
  .header{{margin-bottom:22px;animation:fadeUp .6s ease both}}
  .header-top{{display:flex;align-items:center;gap:10px;margin-bottom:5px}}
  .header-icon{{background:linear-gradient(135deg,#00ff87,#7df9ff);border-radius:8px;padding:7px 10px;font-size:18px;line-height:1}}
  .header-label{{font-size:10px;letter-spacing:4px;color:#7df9ff;text-transform:uppercase}}
  .header-title{{font-size:clamp(18px,4vw,26px);font-weight:900;letter-spacing:-1px}}
  .header-meta{{font-size:11px;color:#555;margin-top:4px}}
  .badge-live{{background:rgba(0,255,135,.1);color:#00ff87;border:1px solid rgba(0,255,135,.25);border-radius:20px;padding:2px 8px;font-size:10px;margin-left:8px}}
  .stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px;animation:fadeUp .6s .1s ease both}}
  .stat-card{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:14px}}
  .stat-label{{font-size:9px;color:#555;margin-bottom:4px}}
  .stat-value{{font-size:17px;font-weight:900;letter-spacing:-.5px}}
  .stat-sub{{font-size:9px;color:#444;margin-top:2px}}
  .info-bar{{background:linear-gradient(135deg,rgba(0,255,135,.05),rgba(125,249,255,.03));border:1px solid rgba(0,255,135,.15);border-radius:12px;padding:14px 18px;margin-bottom:16px;display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;animation:fadeUp .6s .15s ease both}}
  .info-item{{display:flex;gap:8px;align-items:center}}
  .filters{{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:18px;align-items:center;animation:fadeUp .6s .2s ease both}}
  .filter-btn{{padding:7px 18px;border-radius:8px;border:none;cursor:pointer;font-size:12px;font-weight:700;font-family:inherit;background:rgba(255,255,255,.05);color:#777;transition:all .2s}}
  .filter-btn.active{{background:linear-gradient(135deg,#00ff87,#7df9ff);color:#080c12}}
  .cards-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(305px,1fr));gap:13px;margin-bottom:24px}}
  .card{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:15px;padding:17px;cursor:pointer;position:relative;overflow:hidden;transition:all .22s;animation:fadeUp .5s ease both}}
  .card:hover{{border-color:rgba(125,249,255,.18);transform:translateY(-2px)}}
  .card.open{{background:rgba(125,249,255,.04);border-color:rgba(125,249,255,.3)}}
  .card-glow{{position:absolute;top:0;right:0;width:60px;height:60px;border-radius:0 15px 0 0;pointer-events:none}}
  .card-head{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:9px}}
  .card-name{{font-size:13px;font-weight:800;letter-spacing:-.3px;margin-bottom:2px}}
  .card-loc{{font-size:10px;color:#666}}
  .badge{{font-size:8px;padding:2px 6px;border-radius:20px;display:inline-block;margin-bottom:3px}}
  .badge-hot{{background:rgba(255,68,68,.12);color:#ff7777;border:1px solid rgba(255,68,68,.25)}}
  .badge-safe{{background:rgba(0,255,135,.1);color:#00ff87;border:1px solid rgba(0,255,135,.25)}}
  .badge-status{{background:rgba(125,249,255,.07);color:#7df9ff;border:1px solid rgba(125,249,255,.18)}}
  .area-tabs{{display:flex;gap:3px;margin-bottom:10px;background:rgba(0,0,0,.3);border-radius:7px;padding:3px}}
  .area-tab{{flex:1;padding:5px;border-radius:5px;border:none;cursor:pointer;font-size:10px;font-weight:700;font-family:inherit;background:transparent;color:#555;transition:all .15s}}
  .area-tab.active{{background:rgba(125,249,255,.14);color:#7df9ff}}
  .price-grid{{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:10px}}
  .price-box{{background:rgba(0,0,0,.3);border-radius:9px;padding:9px}}
  .price-lbl{{font-size:9px;color:#555;margin-bottom:2px}}
  .price-val{{font-size:13px;font-weight:800}}
  .margin-track{{height:5px;background:rgba(255,255,255,.06);border-radius:3px;overflow:hidden;margin:4px 0 2px}}
  .margin-fill{{height:100%;border-radius:3px;transition:width .6s ease}}
  .card-footer{{display:flex;justify-content:space-between;align-items:center;margin-top:10px}}
  .card-dates{{font-size:9px;color:#555}}
  .badge-dispose{{font-size:9px;padding:2px 6px;border-radius:5px}}
  .badge-dispose.yes{{background:rgba(255,100,100,.08);color:#ff8888}}
  .badge-dispose.no{{background:rgba(0,255,135,.07);color:#00cc6a}}
  .detail{{margin-top:13px;padding-top:13px;border-top:1px solid rgba(255,255,255,.05);animation:fadeIn .25s ease}}
  .detail-grid{{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px}}
  .detail-box{{background:rgba(0,0,0,.28);border-radius:7px;padding:7px 9px}}
  .detail-lbl{{font-size:9px;color:#444;margin-bottom:2px}}
  .detail-val{{font-size:10px;font-weight:700;word-break:break-all}}
  .input-row{{margin-bottom:10px}}
  .input-hint{{font-size:9px;color:#777;margin-bottom:5px}}
  .input-group{{display:flex;gap:5px}}
  .custom-input{{flex:1;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.09);border-radius:6px;padding:6px 9px;color:#dde4f0;font-size:11px;font-family:inherit;outline:none}}
  .reset-btn{{padding:6px 9px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:6px;color:#666;cursor:pointer;font-size:10px;font-family:inherit}}
  .warn-box{{border-radius:8px;padding:10px 11px}}
  .warn-title{{font-size:10px;font-weight:700;margin-bottom:5px}}
  .warn-item{{display:flex;gap:5px;font-size:10px;color:#999;margin-bottom:3px}}
  .no-data{{text-align:center;padding:60px 20px;color:#444;font-size:14px}}
  .footer{{text-align:center;font-size:10px;color:#333;line-height:1.8;padding:14px;background:rgba(255,255,255,.01);border-radius:9px;border:1px solid rgba(255,255,255,.04)}}
  .footer a{{color:#7df9ff;text-decoration:none}}
  @keyframes fadeUp{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
  @keyframes fadeIn{{from{{opacity:0;transform:translateY(5px)}}to{{opacity:1;transform:none}}}}
  ::-webkit-scrollbar{{width:5px}}
  ::-webkit-scrollbar-thumb{{background:rgba(125,249,255,.15);border-radius:3px}}
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow"></div>
<div class="wrap">

  <div class="header">
    <div class="header-top">
      <div class="header-icon">🏢</div>
      <div>
        <div class="header-label">AUTO UPDATE · 공공데이터포털 API</div>
        <div class="header-title">1주택자 청약 안전마진 대시보드</div>
      </div>
    </div>
    <div class="header-meta">
      📅 마지막 업데이트: {updated}
      <span class="badge-live">매일 오전 8시 자동갱신</span>
    </div>
  </div>

  <div class="stats-grid" id="stats-grid">
    <div class="stat-card"><div class="stat-label">수집된 단지</div><div class="stat-value" id="stat-total" style="color:#00ff87">-</div><div class="stat-sub">추첨물량 있는 단지</div></div>
    <div class="stat-card"><div class="stat-label">평균 안전마진</div><div class="stat-value" id="stat-margin" style="color:#7df9ff">-</div><div class="stat-sub">분양가 대비 시세차익</div></div>
    <div class="stat-card"><div class="stat-label">마진 플러스</div><div class="stat-value" id="stat-plus" style="color:#ffd700">-</div><div class="stat-sub">시세 이하 분양 단지</div></div>
    <div class="stat-card"><div class="stat-label">총 추첨 물량</div><div class="stat-value" id="stat-units" style="color:#ff9500">-</div><div class="stat-sub">1주택자 청약 가능</div></div>
  </div>

  <div class="info-bar">
    <div class="info-item"><span style="font-size:18px">🏠</span><div><div style="font-size:9px;color:#777">1주택자 가능 물량</div><div style="font-size:11px;font-weight:700;color:#7df9ff">추첨제 물량만 청약 가능</div></div></div>
    <div class="info-item"><span style="font-size:18px">🎲</span><div><div style="font-size:9px;color:#777">투기과열 추첨 비율</div><div style="font-size:11px;font-weight:700;color:#7df9ff">59㎡↓ 40% / 84㎡↓ 30%</div></div></div>
    <div class="info-item"><span style="font-size:18px">🔓</span><div><div style="font-size:9px;color:#777">비규제지역</div><div style="font-size:11px;font-weight:700;color:#7df9ff">85㎡↓ 60% / 1순위 가능</div></div></div>
    <div class="info-item"><span style="font-size:18px">⚠️</span><div><div style="font-size:9px;color:#777">투기과열 당첨 시</div><div style="font-size:11px;font-weight:700;color:#7df9ff">기존 주택 처분조건 필수확인</div></div></div>
  </div>

  <div class="filters">
    <button class="filter-btn active" onclick="setRegion('전체',this)">전체</button>
    <button class="filter-btn" onclick="setRegion('서울',this)">서울</button>
    <button class="filter-btn" onclick="setRegion('경기',this)">경기</button>
    <button class="filter-btn" onclick="setRegion('지방',this)">지방</button>
    <span style="margin-left:auto;font-size:10px;color:#444">↕ 안전마진 높은 순</span>
  </div>

  <div class="cards-grid" id="cards"></div>

  <div class="footer">
    공공데이터포털 한국부동산원 청약정보 API 기반 · 주변시세는 수동 입력값 사용 ·
    실제 청약 전 <a href="https://www.applyhome.co.kr" target="_blank">청약홈(applyhome.co.kr)</a> 공고문 원문을 반드시 확인하세요 ·
    투자 손실 책임은 본인에게 있습니다
  </div>
</div>

<script>
// ── 자동 수집 데이터 (GitHub Actions가 매일 주입) ──
const RAW_DATA = {cards_js};

// ── 주변시세 수동 설정 (nearby_prices.json에서 관리) ──
const NEARBY = {nearby_js};

let currentRegion = "전체";
let areaTabs = {{}};
let customPrices = {{}};
let openCards = {{}};

function fmt(p) {{
  if (!p || p === 0) return "미정";
  p = parseInt(p);
  if (p >= 10000) {{ const u=Math.floor(p/10000),m=p%10000; return m>0?`${{u}}억 ${{m.toLocaleString()}}만`:`${{u}}억`; }}
  return `${{p.toLocaleString()}}만`;
}}
function mColor(pct) {{
  if (pct >= 20) return "#00ff87";
  if (pct >= 10) return "#7df9ff";
  if (pct >= 0)  return "#ffd700";
  if (pct >= -5) return "#ff9500";
  return "#ff4444";
}}
function mLabel(pct) {{
  if (pct >= 20) return "🔥 로또급";
  if (pct >= 10) return "✅ 우량";
  if (pct >= 0)  return "👍 양호";
  if (pct >= -5) return "⚠️ 주의";
  return "❌ 손실";
}}
function getArea(id) {{ return areaTabs[id] || "84"; }}

function setRegion(r, btn) {{
  currentRegion = r;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  render();
}}
function toggleCard(id) {{ openCards[id] = !openCards[id]; render(); }}
function setAreaTab(id, area) {{ areaTabs[id] = area; render(); }}
function updateCustomPrice(id, area, val) {{
  const v = parseInt(val);
  if (!isNaN(v) && v > 0) customPrices[`${{id}}_${{area}}`] = v;
  else delete customPrices[`${{id}}_${{area}}`];
  render();
}}
function resetPrice(id, area) {{ delete customPrices[`${{id}}_${{area}}`]; render(); }}

function processData() {{
  return RAW_DATA.map(apt => {{
    const a = getArea(apt.id);
    const t = a === "59" ? apt.type59 : apt.type84;
    const sp = t ? parseInt(t.supplyPrice || 0) : 0;
    const nearbyKey = `${{apt.id}}_${{a}}`;
    const manualNearby = NEARBY[nearbyKey] || NEARBY[String(apt.id)] || 0;
    const np = customPrices[nearbyKey] || manualNearby;
    const diff = np && sp ? np - sp : 0;
    const pct = sp && np ? Math.round((diff/sp)*100) : null;
    const lu = t ? parseInt(t.lotteryCount || 0) : 0;
    const lr = t ? parseInt(t.lotteryRatio || 0) : 0;
    return {{ ...apt, a, sp, np, diff, pct, lu, lr, t }};
  }}).filter(s => currentRegion === "전체" ||
    s.region === currentRegion ||
    (currentRegion === "지방" && !["서울","경기","인천"].includes(s.region))
  ).sort((a,b) => (b.pct??-999) - (a.pct??-999));
}}

function updateStats(data) {{
  document.getElementById('stat-total').textContent = data.length + "건";
  const withMargin = data.filter(d => d.pct !== null);
  const avg = withMargin.length ? Math.round(withMargin.reduce((s,d)=>s+d.pct,0)/withMargin.length) : 0;
  document.getElementById('stat-margin').textContent = (avg>0?"+":"") + avg + "%";
  document.getElementById('stat-plus').textContent = data.filter(d=>d.pct>0).length + "/" + data.length + "개";
  const totalUnits = data.reduce((s,d)=>s+(d.lu||0),0);
  document.getElementById('stat-units').textContent = totalUnits.toLocaleString() + "세대";
}}

function render() {{
  const data = processData();
  updateStats(data);
  const container = document.getElementById('cards');
  if (data.length === 0) {{
    container.innerHTML = '<div class="no-data">📭 해당 지역의 청약 단지가 없습니다</div>';
    return;
  }}
  container.innerHTML = data.map((apt, i) => {{
    const mc = apt.pct !== null ? mColor(apt.pct) : "#555";
    const isOpen = openCards[apt.id];
    const curA = apt.a;
    const barW = apt.pct !== null ? Math.min(100,Math.max(2,apt.pct*2)) : 0;
    const regulated = apt.region === "서울" || apt.region === "경기";
    const warns = regulated ? [
      "당첨 후 기존 주택 처분조건 공고문 확인 필수",
      `추첨 가능: 59㎡이하 40% / 84㎡이하 30%`,
      "분양가상한제 단지 실거주 의무 2~5년 확인",
      "잔금대출 25억초과 최대 2억 / 15~25억 최대 4억",
    ] : [
      "1주택자 1순위 청약 가능 (처분조건 없음)",
      `85㎡이하 ${{apt.lr}}% 추첨 / 85㎡초과 100% 추첨`,
      "전매제한 없음",
      "실거주 의무 없음",
    ];
    return `
    <div class="card${{isOpen?' open':''}}" style="animation-delay:${{i*0.05}}s" onclick="toggleCard('${{apt.id}}')">
      <div class="card-glow" style="background:radial-gradient(circle,${{mc}}15 0%,transparent 70%)"></div>
      <div class="card-head">
        <div>
          <div class="card-name">${{apt.name}}</div>
          <div class="card-loc">${{apt.location}}</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:3px;align-items:flex-end">
          <span class="badge ${{regulated?'badge-hot':'badge-safe'}}">${{regulated?'투기과열':'비규제'}}</span>
          <span class="badge badge-status">${{apt.status}}</span>
        </div>
      </div>
      <div class="area-tabs" onclick="event.stopPropagation()">
        <button class="area-tab${{curA==='59'?' active':''}}" onclick="setAreaTab('${{apt.id}}','59')">59㎡</button>
        <button class="area-tab${{curA==='84'?' active':''}}" onclick="setAreaTab('${{apt.id}}','84')">84㎡</button>
      </div>
      <div class="price-grid">
        <div class="price-box"><div class="price-lbl">분양가</div><div class="price-val">${{fmt(apt.sp)}}</div></div>
        <div class="price-box"><div class="price-lbl">주변시세</div><div class="price-val" style="color:#7df9ff">${{apt.np?fmt(apt.np):'직접입력필요'}}</div></div>
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:3px">
          <span style="font-size:10px;color:#777">안전마진</span>
          <span style="font-size:11px;font-weight:800;color:${{mc}}">${{apt.pct!==null?mLabel(apt.pct)+' '+(apt.pct>0?'+':'')+apt.pct+'%':'시세 미입력'}}</span>
        </div>
        <div class="margin-track"><div class="margin-fill" style="width:${{barW}}%;background:linear-gradient(90deg,${{mc}}66,${{mc}})"></div></div>
        <div style="font-size:10px;color:#444">차익: ${{apt.diff?fmt(apt.diff):'미정'}} &nbsp;·&nbsp; 추첨 ${{apt.lu}}세대</div>
      </div>
      <div class="card-footer">
        <div class="card-dates">입주 ${{apt.moveInDate||'미정'}} &nbsp;·&nbsp; 청약 ${{apt.recruitDate||'미정'}}</div>
        <span class="badge-dispose ${{regulated?'yes':'no'}}">${{regulated?'처분조건있음':'처분조건없음'}}</span>
      </div>
      ${{isOpen ? `
      <div class="detail">
        <div class="detail-title">📊 상세 분석</div>
        <div class="detail-grid">
          <div class="detail-box"><div class="detail-lbl">총 세대수</div><div class="detail-val">${{apt.supplyCount||'-'}}세대</div></div>
          <div class="detail-box"><div class="detail-lbl">시공사</div><div class="detail-val">${{apt.constructor||'-'}}</div></div>
          <div class="detail-box"><div class="detail-lbl">청약 접수</div><div class="detail-val">${{apt.recruitDate||'-'}} ~ ${{apt.recruitEndDate||'-'}}</div></div>
          <div class="detail-box"><div class="detail-lbl">당첨자 발표</div><div class="detail-val">${{apt.winnerDate||'-'}}</div></div>
        </div>
        <div class="input-row" onclick="event.stopPropagation()">
          <div class="input-hint">📌 주변 시세 입력 (만원) — 입력 시 마진 자동 재계산</div>
          <div class="input-group">
            <input class="custom-input" type="number" placeholder="${{apt.np||'예: 80000 (8억)'}}"
              oninput="updateCustomPrice('${{apt.id}}','${{curA}}',this.value)" />
            <button class="reset-btn" onclick="resetPrice('${{apt.id}}','${{curA}}')">↩</button>
          </div>
        </div>
        <div class="warn-box" style="background:${{regulated?'rgba(255,68,68,.04)':'rgba(0,255,135,.03)'}};border:1px solid ${{regulated?'rgba(255,68,68,.12)':'rgba(0,255,135,.12)'}}">
          <div class="warn-title" style="color:${{regulated?'#ff8888':'#00ff87'}}">${{regulated?'⚠️ 투기과열 1주택 유의사항':'✅ 비규제 1주택자 청약 혜택'}}</div>
          ${{warns.map(w=>`<div class="warn-item"><span style="color:${{regulated?'#ff8888':'#00ff87'}};flex-shrink:0">•</span>${{w}}</div>`).join('')}}
        </div>
      </div>` : ''}}
    </div>`;
  }}).join('');
}}

render();
</script>
</body>
</html>"""
    return html

if __name__ == "__main__":
    # 주변시세 파일 로드 (없으면 빈값)
    try:
        with open("nearby_prices.json", "r", encoding="utf-8") as f:
            manual_nearby = json.load(f)
    except:
        manual_nearby = {}

    dataset = build_dataset()

    # HTML 생성
    html = generate_html(dataset, manual_nearby)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    # 데이터 캐시 저장
    with open("docs/data.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"✅ 완료! docs/index.html 생성됨 ({len(dataset)}개 단지)")
