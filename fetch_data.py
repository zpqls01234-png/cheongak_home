
"""
청약홈 데이터 자동 수집 스크립트
공공데이터포털 한국부동산원 청약정보 API 사용
"""
import requests
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

API_KEY = os.environ.get(“PUBLIC_DATA_API_KEY”, “”)

# 올바른 엔드포인트 (분양정보 조회 서비스)

BASE_URL = “http://apis.data.go.kr/B552555/APTLttotPblancDetail”

def fetch_apt_list():
“”“아파트 분양 공고 목록 조회”””
today = datetime.now()
url = f”{BASE_URL}/getLttotPblancList”
params = {
“serviceKey”: API_KEY,
“startMonth”: (today - timedelta(days=30)).strftime(”%Y%m”),
“endMonth”: today.strftime(”%Y%m”),
“numOfRows”: “100”,
“pageNo”: “1”,
}
try:
res = requests.get(url, params=params, timeout=20)
print(f”  [API] 상태코드: {res.status_code}”)
root = ET.fromstring(res.content)

```
    # 에러 체크
    result_code = root.findtext(".//resultCode", "")
    if result_code not in ("00", "0000", ""):
        print(f"  [API] 오류: {root.findtext('.//resultMsg','')}")
        return []

    items = root.findall(".//item")
    result = []
    for item in items:
        def g(tag):
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""

        rcpt_bgnde = g("RCEPT_BGNDE")
        rcpt_endde = g("RCEPT_ENDDE")
        today_str = today.strftime("%Y%m%d")
        if rcpt_bgnde and rcpt_endde:
            status = "진행중" if rcpt_bgnde <= today_str <= rcpt_endde else "예정"
        else:
            status = "예정"

        result.append({
            "id": g("HOUSE_MANAGE_NO"),
            "name": g("HOUSE_NM"),
            "location": g("HSSPLY_ADRES"),
            "region": g("SUBSCRPT_AREA_CODE_NM"),
            "supplyCount": g("TOT_SUPLY_HSHLDCO"),
            "recruitDate": rcpt_bgnde,
            "recruitEndDate": rcpt_endde,
            "winnerDate": g("PRZWNER_PRESNATN_DE"),
            "moveInDate": g("MOVE_IN_YM"),
            "constructor": g("BSNS_MBY_NM"),
            "houseType": g("HOUSE_SECD_NM"),
            "status": status,
            "type59": None,
            "type84": None,
        })
    return result
except Exception as e:
    print(f"  [ERROR] 목록 조회 실패: {e}")
    return []
```

def fetch_apt_detail(manage_no):
“”“단지별 타입/분양가 상세 조회”””
url = f”{BASE_URL}/getLttotPblancDetail”
params = {
“serviceKey”: API_KEY,
“houseManageNo”: manage_no,
“numOfRows”: “50”,
“pageNo”: “1”,
}
try:
res = requests.get(url, params=params, timeout=20)
root = ET.fromstring(res.content)
items = root.findall(”.//item”)
types = []
for item in items:
def g(tag):
el = item.find(tag)
return (el.text or “”).strip() if el is not None else “”

```
        lottery = g("CHCSR_HSHLDCO") or "0"
        total_supply = g("SUPLY_HSHLDCO") or "1"
        try:
            lr = round(int(lottery) / max(int(total_supply), 1) * 100)
        except:
            lr = 0

        price_str = g("LTTOT_TOP_AMOUNT")
        try:
            price = int(price_str) * 10000 if price_str else 0
        except:
            price = 0

        types.append({
            "houseTy": g("HOUSE_TY"),
            "area": g("SUPLY_AR"),
            "supplyCount": g("SUPLY_HSHLDCO"),
            "lotteryCount": lottery,
            "gajeomCount": g("GAGYM_HSHLDCO") or "0",
            "supplyPrice": price,
            "lotteryRatio": lr,
        })
    return types
except Exception as e:
    print(f"  [ERROR] 상세 조회 실패 ({manage_no}): {e}")
    return []
```

def build_dataset():
print(f”[{datetime.now().strftime(’%Y-%m-%d %H:%M’)}] 청약 데이터 수집 시작…”)
apts = fetch_apt_list()
print(f”  → 공고 {len(apts)}건 수집”)

```
dataset = []
for apt in apts:
    types = fetch_apt_detail(apt["id"])

    # 추첨 물량 있는 단지만 포함
    has_lottery = any(int(t.get("lotteryCount","0") or "0") > 0 for t in types)
    if not has_lottery:
        continue

    # 59㎡, 84㎡ 타입 추출
    t59 = next((t for t in types if "59" in str(t.get("area",""))), None)
    t84 = next((t for t in types if "84" in str(t.get("area",""))), None)

    apt["type59"] = t59
    apt["type84"] = t84
    dataset.append(apt)

print(f"  → 1주택자 추첨물량 있는 단지: {len(dataset)}건")
return dataset
```

def generate_html(dataset, manual_nearby):
updated = datetime.now().strftime(”%Y.%m.%d %H:%M”)
cards_js = json.dumps(dataset, ensure_ascii=False)
nearby_js = json.dumps(manual_nearby, ensure_ascii=False)

```
return f"""<!DOCTYPE html>
```

<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>1주택자 청약 안전마진 대시보드</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#080c12;color:#dde4f0;font-family:'Noto Sans KR','Apple SD Gothic Neo',sans-serif;min-height:100vh}}
.bg{{position:fixed;inset:0;opacity:.03;pointer-events:none;background-image:linear-gradient(rgba(0,255,135,1) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,135,1) 1px,transparent 1px);background-size:48px 48px}}
.wrap{{max-width:1080px;margin:0 auto;padding:28px 16px;position:relative;z-index:1}}
.header{{margin-bottom:22px}}
.header-top{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
.icon{{background:linear-gradient(135deg,#00ff87,#7df9ff);border-radius:8px;padding:7px 10px;font-size:18px}}
.title{{font-size:clamp(18px,4vw,26px);font-weight:900;letter-spacing:-1px}}
.sublabel{{font-size:10px;letter-spacing:4px;color:#7df9ff;text-transform:uppercase}}
.meta{{font-size:11px;color:#555;margin-top:4px}}
.badge-live{{background:rgba(0,255,135,.1);color:#00ff87;border:1px solid rgba(0,255,135,.25);border-radius:20px;padding:2px 8px;font-size:10px;margin-left:8px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:16px}}
.scard{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:14px}}
.slabel{{font-size:9px;color:#555;margin-bottom:4px}}
.sval{{font-size:17px;font-weight:900}}
.ssub{{font-size:9px;color:#444;margin-top:2px}}
.infobar{{background:linear-gradient(135deg,rgba(0,255,135,.05),rgba(125,249,255,.03));border:1px solid rgba(0,255,135,.15);border-radius:12px;padding:14px 18px;margin-bottom:16px;display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}
.iitem{{display:flex;gap:8px;align-items:center}}
.filters{{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:18px;align-items:center}}
.fbtn{{padding:7px 18px;border-radius:8px;border:none;cursor:pointer;font-size:12px;font-weight:700;font-family:inherit;background:rgba(255,255,255,.05);color:#777;transition:all .2s}}
.fbtn.on{{background:linear-gradient(135deg,#00ff87,#7df9ff);color:#080c12}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(305px,1fr));gap:13px;margin-bottom:24px}}
.card{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:15px;padding:17px;cursor:pointer;position:relative;overflow:hidden;transition:border-color .2s,transform .2s}}
.card:hover{{border-color:rgba(125,249,255,.2);transform:translateY(-2px)}}
.card.open{{background:rgba(125,249,255,.04);border-color:rgba(125,249,255,.3)}}
.cglow{{position:absolute;top:0;right:0;width:60px;height:60px;border-radius:0 15px 0 0;pointer-events:none}}
.chead{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:9px}}
.cname{{font-size:13px;font-weight:800;letter-spacing:-.3px;margin-bottom:2px}}
.cloc{{font-size:10px;color:#666}}
.badge{{font-size:8px;padding:2px 6px;border-radius:20px;display:block;margin-bottom:3px;text-align:center}}
.b-hot{{background:rgba(255,68,68,.12);color:#ff7777;border:1px solid rgba(255,68,68,.25)}}
.b-safe{{background:rgba(0,255,135,.1);color:#00ff87;border:1px solid rgba(0,255,135,.25)}}
.b-st{{background:rgba(125,249,255,.07);color:#7df9ff;border:1px solid rgba(125,249,255,.18)}}
.atabs{{display:flex;gap:3px;margin-bottom:10px;background:rgba(0,0,0,.3);border-radius:7px;padding:3px}}
.atab{{flex:1;padding:5px;border-radius:5px;border:none;cursor:pointer;font-size:10px;font-weight:700;font-family:inherit;background:transparent;color:#555;transition:all .15s}}
.atab.on{{background:rgba(125,249,255,.14);color:#7df9ff}}
.pgrid{{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:10px}}
.pbox{{background:rgba(0,0,0,.3);border-radius:9px;padding:9px}}
.plbl{{font-size:9px;color:#555;margin-bottom:2px}}
.pval{{font-size:13px;font-weight:800}}
.mtrack{{height:5px;background:rgba(255,255,255,.06);border-radius:3px;overflow:hidden;margin:4px 0 2px}}
.mfill{{height:100%;border-radius:3px;transition:width .6s}}
.cfooter{{display:flex;justify-content:space-between;align-items:center;margin-top:10px}}
.cdates{{font-size:9px;color:#555}}
.bdis{{font-size:9px;padding:2px 6px;border-radius:5px}}
.bdis.yes{{background:rgba(255,100,100,.08);color:#ff8888}}
.bdis.no{{background:rgba(0,255,135,.07);color:#00cc6a}}
.detail{{margin-top:13px;padding-top:13px;border-top:1px solid rgba(255,255,255,.05)}}
.dgrid{{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px}}
.dbox{{background:rgba(0,0,0,.28);border-radius:7px;padding:7px 9px}}
.dlbl{{font-size:9px;color:#444;margin-bottom:2px}}
.dval{{font-size:10px;font-weight:700;word-break:break-all}}
.irow{{margin-bottom:10px}}
.ihint{{font-size:9px;color:#777;margin-bottom:5px}}
.igrp{{display:flex;gap:5px}}
.cinput{{flex:1;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.09);border-radius:6px;padding:6px 9px;color:#dde4f0;font-size:11px;font-family:inherit;outline:none}}
.rbtn{{padding:6px 9px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:6px;color:#666;cursor:pointer;font-family:inherit}}
.wbox{{border-radius:8px;padding:10px 11px}}
.wtitle{{font-size:10px;font-weight:700;margin-bottom:5px}}
.witem{{display:flex;gap:5px;font-size:10px;color:#999;margin-bottom:3px}}
.nodata{{text-align:center;padding:60px;color:#444}}
.footer{{text-align:center;font-size:10px;color:#333;line-height:1.8;padding:14px;background:rgba(255,255,255,.01);border-radius:9px;border:1px solid rgba(255,255,255,.04)}}
.footer a{{color:#7df9ff;text-decoration:none}}
::-webkit-scrollbar{{width:5px}}
::-webkit-scrollbar-thumb{{background:rgba(125,249,255,.15);border-radius:3px}}
</style>
</head>
<body>
<div class="bg"></div>
<div class="wrap">
  <div class="header">
    <div class="header-top">
      <div class="icon">🏢</div>
      <div>
        <div class="sublabel">AUTO UPDATE · 공공데이터포털 API</div>
        <div class="title">1주택자 청약 안전마진 대시보드</div>
      </div>
    </div>
    <div class="meta">📅 마지막 업데이트: {updated} <span class="badge-live">매일 오전 8시 자동갱신</span></div>
  </div>

  <div class="stats">
    <div class="scard"><div class="slabel">수집된 단지</div><div class="sval" id="s1" style="color:#00ff87">-</div><div class="ssub">추첨물량 있는 단지</div></div>
    <div class="scard"><div class="slabel">평균 안전마진</div><div class="sval" id="s2" style="color:#7df9ff">-</div><div class="ssub">시세 입력 단지 기준</div></div>
    <div class="scard"><div class="slabel">마진 플러스</div><div class="sval" id="s3" style="color:#ffd700">-</div><div class="ssub">시세 이하 분양 단지</div></div>
    <div class="scard"><div class="slabel">총 추첨 물량</div><div class="sval" id="s4" style="color:#ff9500">-</div><div class="ssub">1주택자 청약 가능</div></div>
  </div>

  <div class="infobar">
    <div class="iitem"><span style="font-size:18px">🏠</span><div><div style="font-size:9px;color:#777">1주택자 가능 물량</div><div style="font-size:11px;font-weight:700;color:#7df9ff">추첨제 물량만 청약 가능</div></div></div>
    <div class="iitem"><span style="font-size:18px">🎲</span><div><div style="font-size:9px;color:#777">투기과열 추첨 비율</div><div style="font-size:11px;font-weight:700;color:#7df9ff">59㎡↓ 40% / 84㎡↓ 30%</div></div></div>
    <div class="iitem"><span style="font-size:18px">🔓</span><div><div style="font-size:9px;color:#777">비규제지역</div><div style="font-size:11px;font-weight:700;color:#7df9ff">85㎡↓ 60% / 1순위 가능</div></div></div>
    <div class="iitem"><span style="font-size:18px">⚠️</span><div><div style="font-size:9px;color:#777">투기과열 당첨 시</div><div style="font-size:11px;font-weight:700;color:#7df9ff">기존 주택 처분조건 필수확인</div></div></div>
  </div>

  <div class="filters">
    <button class="fbtn on" onclick="setR('전체',this)">전체</button>
    <button class="fbtn" onclick="setR('서울',this)">서울</button>
    <button class="fbtn" onclick="setR('경기',this)">경기</button>
    <button class="fbtn" onclick="setR('지방',this)">지방</button>
    <span style="margin-left:auto;font-size:10px;color:#444">↕ 안전마진 높은 순</span>
  </div>

  <div class="grid" id="cards"></div>

  <div class="footer">
    공공데이터포털 한국부동산원 청약정보 API 기반 · 주변시세는 카드 클릭 후 직접 입력 ·
    실제 청약 전 <a href="https://www.applyhome.co.kr" target="_blank">청약홈</a> 공고문 원문을 반드시 확인하세요
  </div>
</div>
<script>
const RAW={cards_js};
const NEARBY={nearby_js};
let region='전체',tabs={{}},custom={{}},open={{}};

const fmt=p=>{{
if(!p||p===0)return’미정’;p=parseInt(p);
if(p>=10000){{const u=Math.floor(p/10000),m=p%10000;return m?`${{u}}억 ${{m.toLocaleString()}}만`:`${{u}}억`;}}
return`${{p.toLocaleString()}}만`;
}};
const mc=p=>p>=20?’#00ff87’:p>=10?’#7df9ff’:p>=0?’#ffd700’:p>=-5?’#ff9500’:’#ff4444’;
const ml=p=>p>=20?‘🔥 로또급’:p>=10?‘✅ 우량’:p>=0?‘👍 양호’:p>=-5?‘⚠️ 주의’:‘❌ 손실’;
const ga=id=>tabs[id]||‘84’;

function setR(r,btn){{region=r;document.querySelectorAll(’.fbtn’).forEach(b=>b.classList.remove(‘on’));btn.classList.add(‘on’);render();}}
function tog(id){{open[id]=!open[id];render();}}
function setA(id,a){{tabs[id]=a;render();}}
function upd(id,a,v){{const n=parseInt(v);if(!isNaN(n)&&n>0)custom[`${{id}}_${{a}}`]=n;else delete custom[`${{id}}_${{a}}`];render();}}
function rst(id,a){{delete custom[`${{id}}_${{a}}`];render();}}

function proc(){{
const SEOULGYEONGGI=[‘서울’,‘경기’,‘인천’];
return RAW.map(apt=>{{
const a=ga(apt.id),t=a===‘59’?apt.type59:apt.type84;
const sp=t?parseInt(t.supplyPrice||0):0;
const nk=`${{apt.id}}_${{a}}`;
const np=custom[nk]||NEARBY[nk]||NEARBY[apt.id]||0;
const diff=np&&sp?np-sp:0;
const pct=sp&&np?Math.round((diff/sp)*100):null;
const lu=t?parseInt(t.lotteryCount||0):0;
const lr=t?parseInt(t.lotteryRatio||0):0;
const reg=SEOULGYEONGGI.includes(apt.region);
return{{…apt,a,sp,np,diff,pct,lu,lr,reg}};
}}).filter(s=>region===‘전체’||s.region===region||(region===‘지방’&&![‘서울’,‘경기’,‘인천’].includes(s.region)))
.sort((a,b)=>(b.pct??-999)-(a.pct??-999));
}}

function render(){{
const data=proc();
// stats
document.getElementById(‘s1’).textContent=data.length+‘건’;
const wm=data.filter(d=>d.pct!==null);
const avg=wm.length?Math.round(wm.reduce((s,d)=>s+d.pct,0)/wm.length):0;
document.getElementById(‘s2’).textContent=(avg>0?’+’:’’)+avg+’%’;
document.getElementById(‘s3’).textContent=data.filter(d=>d.pct>0).length+’/’+data.length+‘개’;
document.getElementById(‘s4’).textContent=data.reduce((s,d)=>s+(d.lu||0),0).toLocaleString()+‘세대’;

const el=document.getElementById(‘cards’);
if(!data.length){{el.innerHTML=’<div class="nodata">📭 해당 지역 청약 단지 없음</div>’;return;}}

el.innerHTML=data.map((apt,i)=>{{
const c=apt.pct!==null?mc(apt.pct):’#555’;
const isO=open[apt.id];
const bw=apt.pct!==null?Math.min(100,Math.max(2,apt.pct*2)):0;
const warns=apt.reg?[
‘당첨 후 기존 주택 처분조건 공고문 확인 필수’,
‘추첨 가능: 59㎡이하 40% / 84㎡이하 30%’,
‘분양가상한제 단지 실거주 의무 2~5년 확인’,
’잔금대출 25억초과 최대2억 / 15~25억 최대4억’,
]:[
‘1주택자 1순위 청약 가능 (처분조건 없음)’,
`85㎡이하 ${{apt.lr}}% 추첨 / 85㎡초과 100% 추첨`,
‘전매제한 없음 — 계약 후 즉시 전매 가능’,
‘실거주 의무 없음’,
];
const curA=apt.a;
return`<div class="card${{isO?' open':''}}" onclick="tog('${{apt.id}}')"> <div class="cglow" style="background:radial-gradient(circle,${{c}}15 0%,transparent 70%)"></div> <div class="chead"> <div><div class="cname">${{apt.name}}</div><div class="cloc">${{apt.location}}</div></div> <div><span class="badge ${{apt.reg?'b-hot':'b-safe'}}">${{apt.reg?'투기과열':'비규제'}}</span><span class="badge b-st">${{apt.status}}</span></div> </div> <div class="atabs" onclick="event.stopPropagation()"> <button class="atab${{curA==='59'?' on':''}}" onclick="setA('${{apt.id}}','59')">59㎡</button> <button class="atab${{curA==='84'?' on':''}}" onclick="setA('${{apt.id}}','84')">84㎡</button> </div> <div class="pgrid"> <div class="pbox"><div class="plbl">분양가</div><div class="pval">${{fmt(apt.sp)}}</div></div> <div class="pbox"><div class="plbl">주변시세</div><div class="pval" style="color:#7df9ff">${{apt.np?fmt(apt.np):'직접입력'}}</div></div> </div> <div> <div style="display:flex;justify-content:space-between;margin-bottom:3px"> <span style="font-size:10px;color:#777">안전마진</span> <span style="font-size:11px;font-weight:800;color:${{c}}">${{apt.pct!==null?ml(apt.pct)+' '+(apt.pct>0?'+':'')+apt.pct+'%':'시세 미입력'}}</span> </div> <div class="mtrack"><div class="mfill" style="width:${{bw}}%;background:linear-gradient(90deg,${{c}}66,${{c}})"></div></div> <div style="font-size:10px;color:#444">차익: ${{apt.diff?fmt(apt.diff):'미정'}} · 추첨 ${{apt.lu}}세대</div> </div> <div class="cfooter"> <div class="cdates">입주 ${{apt.moveInDate||'미정'}} · 청약 ${{apt.recruitDate||'미정'}}</div> <span class="bdis ${{apt.reg?'yes':'no'}}">${{apt.reg?'처분조건있음':'처분조건없음'}}</span> </div> ${{isO?`<div class="detail">
<div style="font-size:10px;color:#7df9ff;font-weight:700;margin-bottom:9px">📊 상세 분석</div>
<div class="dgrid">
<div class="dbox"><div class="dlbl">총 세대수</div><div class="dval">${{apt.supplyCount||’-’}}세대</div></div>
<div class="dbox"><div class="dlbl">시공사</div><div class="dval">${{apt.constructor||’-’}}</div></div>
<div class="dbox"><div class="dlbl">청약 접수</div><div class="dval">${{apt.recruitDate||’-’}}~${{apt.recruitEndDate||’-’}}</div></div>
<div class="dbox"><div class="dlbl">당첨자 발표</div><div class="dval">${{apt.winnerDate||’-’}}</div></div>
</div>
<div class="irow" onclick="event.stopPropagation()">
<div class="ihint">📌 주변 시세 입력 (만원) — 마진 자동 재계산</div>
<div class="igrp">
<input class="cinput" type="number" placeholder="${{apt.np||'예: 80000 (8억)'}}" oninput="upd('${{apt.id}}','${{curA}}',this.value)"/>
<button class="rbtn" onclick="rst('${{apt.id}}','${{curA}}')">↩</button>
</div>
</div>
<div class="wbox" style="background:${{apt.reg?'rgba(255,68,68,.04)':'rgba(0,255,135,.03)'}};border:1px solid ${{apt.reg?'rgba(255,68,68,.12)':'rgba(0,255,135,.12)'}}">
<div class="wtitle" style="color:${{apt.reg?'#ff8888':'#00ff87'}}">${{apt.reg?‘⚠️ 투기과열 1주택 유의사항’:‘✅ 비규제 1주택자 청약 혜택’}}</div>
${{warns.map(w=>`<div class="witem"><span style="color:${{apt.reg?'#ff8888':'#00ff87'}};flex-shrink:0">•</span>${{w}}</div>`).join(’’)}}
</div>
</div>`:''}}</div>`;
}}).join(’’);
}}
render();
</script>

</body>
</html>"""

if **name** == “**main**”:
# docs 폴더 자동 생성 (핵심 수정!)
os.makedirs(“docs”, exist_ok=True)

```
# 주변시세 파일 로드
try:
    with open("nearby_prices.json", "r", encoding="utf-8") as f:
        manual_nearby = json.load(f)
except:
    manual_nearby = {}

dataset = build_dataset()
html = generate_html(dataset, manual_nearby)

with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(html)

with open("docs/data.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print(f"✅ 완료! docs/index.html 생성됨 ({len(dataset)}개 단지)")
```
