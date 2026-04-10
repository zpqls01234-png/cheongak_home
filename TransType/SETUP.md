# TransType - iOS Custom Keyboard Extension

한국어 입력을 실시간으로 영어/일본어로 번역하는 iOS 커스텀 키보드 앱입니다.

## 프로젝트 구조

```
TransType/
├── TransTypeApp/                         # 메인 앱 (Host App)
│   ├── TransTypeApp.swift                # @main 앱 진입점
│   ├── ContentView.swift                 # 설정 화면 + 테스트 입력 필드
│   ├── OnboardingView.swift              # 키보드 활성화 가이드
│   ├── Info.plist                        # 메인 앱 설정
│   └── Assets.xcassets/                  # 앱 아이콘, 색상 등
├── TransTypeKeyboard/                    # 키보드 익스텐션
│   ├── KeyboardViewController.swift      # UIInputViewController 서브클래스
│   ├── TranslationBarView.swift          # 번역 결과 표시 UI (상단 바)
│   ├── TranslationService.swift          # 번역 로직 (디바운스 + 사전 기반)
│   ├── LanguageManager.swift             # 번역 대상 언어 관리
│   └── Info.plist                        # 키보드 익스텐션 설정
├── Shared/                               # 메인앱-익스텐션 공유 코드
│   ├── UserDefaultsKeys.swift            # App Group 공유 설정
│   └── SupportedLanguage.swift           # 지원 언어 enum
└── SETUP.md                              # 이 파일
```

## Xcode 프로젝트 셋업 가이드

### 1단계: 새 Xcode 프로젝트 생성

1. Xcode를 열고 **File → New → Project** 선택
2. **App** 템플릿 선택
3. 프로젝트 설정:
   - Product Name: `TransType`
   - Team: 본인의 개발자 팀 선택
   - Organization Identifier: `com.transtype`
   - Interface: **SwiftUI**
   - Language: **Swift**
   - Minimum Deployments: **iOS 16.0**
4. 프로젝트 저장 위치 선택

### 2단계: 키보드 익스텐션 타겟 추가

1. **File → New → Target** 선택
2. **Custom Keyboard Extension** 선택
3. 설정:
   - Product Name: `TransTypeKeyboard`
   - Language: **Swift**
   - "Activate" 클릭하여 스킴 활성화

### 3단계: App Group 설정

1. 프로젝트 네비게이터에서 프로젝트 파일 선택
2. **TransType** 타겟 → **Signing & Capabilities** 탭
3. **+ Capability** → **App Groups** 추가
4. `group.com.transtype.shared` 그룹 추가
5. **TransTypeKeyboard** 타겟에서도 동일하게 App Group 추가
   - 같은 `group.com.transtype.shared` 선택

### 4단계: 소스 파일 추가

#### 메인 앱 타겟 (TransType):
1. 기존 자동 생성된 `ContentView.swift` 삭제
2. 기존 자동 생성된 앱 엔트리 포인트 파일 삭제
3. 다음 파일들을 TransType 타겟에 추가:
   - `TransTypeApp/TransTypeApp.swift`
   - `TransTypeApp/ContentView.swift`
   - `TransTypeApp/OnboardingView.swift`
   - `Shared/SupportedLanguage.swift` (Target Membership: 양쪽 타겟 모두)
   - `Shared/UserDefaultsKeys.swift` (Target Membership: 양쪽 타겟 모두)

#### 키보드 익스텐션 타겟 (TransTypeKeyboard):
1. 기존 자동 생성된 `KeyboardViewController.swift` 삭제
2. 다음 파일들을 TransTypeKeyboard 타겟에 추가:
   - `TransTypeKeyboard/KeyboardViewController.swift`
   - `TransTypeKeyboard/TranslationBarView.swift`
   - `TransTypeKeyboard/TranslationService.swift`
   - `TransTypeKeyboard/LanguageManager.swift`
   - `Shared/SupportedLanguage.swift` (이미 추가됨, Target Membership만 확인)
   - `Shared/UserDefaultsKeys.swift` (이미 추가됨, Target Membership만 확인)

### 5단계: Info.plist 설정

#### 키보드 익스텐션 (TransTypeKeyboard/Info.plist):
아래 내용이 포함되어 있는지 확인:
```xml
<key>NSExtension</key>
<dict>
    <key>NSExtensionAttributes</key>
    <dict>
        <key>IsASCIICapable</key>
        <false/>
        <key>PrefersRightToLeft</key>
        <false/>
        <key>PrimaryLanguage</key>
        <string>ko</string>
        <key>RequestsOpenAccess</key>
        <true/>
    </dict>
    <key>NSExtensionPointIdentifier</key>
    <string>com.apple.keyboard-service</string>
    <key>NSExtensionPrincipalClass</key>
    <string>$(PRODUCT_MODULE_NAME).KeyboardViewController</string>
</dict>
```

### 6단계: Shared 파일 Target Membership 설정

1. `SupportedLanguage.swift` 파일 선택
2. 오른쪽 파일 인스펙터에서 **Target Membership**:
   - [x] TransType (메인 앱)
   - [x] TransTypeKeyboard (키보드 익스텐션)
3. `UserDefaultsKeys.swift`에도 동일하게 적용

### 7단계: 빌드 및 테스트

1. 시뮬레이터 또는 실제 디바이스 선택
2. **TransType** 스킴으로 빌드 (Cmd+B)
3. 실행 (Cmd+R)
4. 메인 앱에서 온보딩 가이드를 따라 키보드 활성화
5. 텍스트 입력 필드에서 키보드를 TransType으로 전환
6. 한국어 입력 시 상단 바에 번역 결과 표시 확인

## 주요 기능

### 번역 Suggestion Bar
- 키보드 상단 44pt 높이의 바에 번역 결과 표시
- 레이아웃: `[🇺🇸 English | 🇯🇵 日本語 | ⚙️]`
- 번역 결과 탭 → 한국어 원문 삭제 → 번역 텍스트 삽입

### 실시간 번역
- 0.3초 디바운스로 불필요한 번역 호출 방지
- 한국어 유니코드 범위 자동 감지 (가-힣, ㄱ-ㅎ, ㅏ-ㅣ)
- 오프라인 사전 기반 MVP 번역 (80+ 한→영/일 단어)

### 다크모드 지원
- 시스템 키보드 색상과 조화되는 자동 테마 전환
- 라이트모드: systemGray6, 다크모드: systemGray5

### 메인 앱 설정
- 번역 대상 언어 토글 (영어, 일본어, 중국어, 스페인어)
- 자동 번역 on/off
- 디바운스 간격 조절 (0.1~1.0초)
- 햅틱 피드백 on/off
- 테스트 입력 필드

## 향후 확장 가능 사항

1. **Apple Translation Framework** (iOS 17.4+) 통합으로 온라인 번역 지원
2. 문장 단위 번역 지원
3. 번역 히스토리 저장 및 즐겨찾기
4. 추가 언어 지원 (중국어, 스페인어 사전 확장)
5. 위젯으로 최근 번역 표시

## 요구사항

- Xcode 15.0+
- iOS 16.0+
- Swift 5.9+
