# 🏢 1주택자 청약 안전마진 대시보드

> 공공데이터포털 청약 API를 이용해 매일 자동으로 분양 정보를 수집하고 GitHub Pages로 배포합니다.

## 🚀 세팅 방법 (10분)

### 1. GitHub 저장소 만들기
- GitHub에서 새 저장소 생성 (예: `cheongak-dashboard`)
- 이 폴더 내 파일을 모두 업로드

### 2. API 키 등록
- GitHub 저장소 → Settings → Secrets and variables → Actions
- **New repository secret** 클릭
- Name: `PUBLIC_DATA_API_KEY`
- Value: 공공데이터포털에서 발급받은 API 키

### 3. GitHub Pages 활성화
- 저장소 Settings → Pages
- Source: `Deploy from a branch`
- Branch: `gh-pages` / `/ (root)`
- Save

### 4. 첫 실행
- Actions 탭 → "청약 데이터 매일 자동 업데이트" → Run workflow

### 5. 내 사이트 주소
```
https://[내 GitHub 아이디].github.io/cheongak-dashboard/
```

## 📌 주변 시세 입력 방법
`nearby_prices.json` 파일에서 단지별 시세를 수동으로 관리합니다.
API에서 청약 데이터를 가져온 후 각 단지의 ID를 확인해서 입력하세요.

## 🔄 자동 업데이트 일정
- 매일 오전 8시 (한국 시간) 자동 실행
- Actions 탭에서 수동 실행도 가능

## 📦 사용 API
- 공공데이터포털: 한국부동산원 청약정보 서비스
- https://www.data.go.kr → "아파트분양정보" 검색
