# DART-DB Flet

한국 상장기업(KOSPI/KOSDAQ)의 DART 전자공시 데이터를 수집, 분석, 시각화하는 **Standalone 크로스플랫폼 데스크톱 애플리케이션**입니다.

## 주요 특징

- **Docker/API 서버 불필요**: 단일 실행 파일로 동작
- **로컬 SQLite 데이터베이스**: 설치 없이 내장 DB 사용
- **크로스플랫폼 지원**: Windows, macOS, Linux, Web
- **DART Open API 연동**: 실시간 기업 정보 및 재무제표 수집
- **재무 분석 도구**: 재무비율 계산, 성장률 분석, 기업 비교

## 주요 기능

### 1. 기업 검색 및 목록 조회
- KOSPI/KOSDAQ 상장기업 검색
- 기업 필터링 (시장구분, 업종 등)
- 페이지네이션 지원

### 2. 기업 상세 정보
- 기본 정보 (종목코드, 대표자, 업종 등)
- 3개년 재무제표
- 재무비율 (부채비율, ROE, ROA, 영업이익률 등)

### 3. 재무 분석
- 매출/영업이익 추이 분석
- CAGR (복합성장률) 계산
- 재무 건전성 점수

### 4. 기업 비교
- 최대 5개 기업 동시 비교
- 주요 지표 비교 테이블
- 비교 세트 저장/불러오기

### 5. 데이터 수집
- DART API 연동 설정
- 기업 목록 동기화
- 진행률 실시간 표시

## 시스템 요구사항

### 개발 환경
- Python 3.11 이상
- pip 또는 pipx

### 빌드 환경
- Flutter SDK 3.38+
- Windows: Visual Studio Build Tools
- macOS: Xcode
- Linux: GTK 3.0 development libraries (`apt install libgtk-3-dev`)

## 설치 방법

### 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/gmdjlee/dart-db-flet.git
cd dart-db-flet

# 가상환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -e ".[dev]"
```

### DART API 키 설정

1. [DART Open API](https://opendart.fss.or.kr/) 회원가입
2. 인증키 발급
3. 환경변수 설정:
   ```bash
   export DART_API_KEY="your-api-key"
   ```
   또는 앱 내 설정에서 API 키 입력

## 실행 방법

### 개발 모드

```bash
# Desktop 모드
flet run src/main.py

# Web 모드
flet run src/main.py --web

# 핫 리로드 활성화
flet run src/main.py -r
```

### 직접 실행

```bash
python -m src.main
```

## 빌드 방법

### Windows

```bash
flet build windows src/
```

빌드 결과: `src/build/windows/dart-db-flet.exe`

### macOS

```bash
flet build macos src/
```

빌드 결과: `src/build/macos/dart-db-flet.app`

### Linux

```bash
flet build linux src/
```

빌드 결과: `src/build/linux/dart-db-flet`

### Web

```bash
flet build web src/
```

빌드 결과: `src/build/web/` (정적 파일)

## 프로젝트 구조

```
dart-db-flet/
├── pyproject.toml          # 프로젝트 설정 및 의존성
├── README.md               # 이 파일
├── src/
│   ├── main.py             # 앱 진입점
│   ├── assets/             # 아이콘, 스플래시 이미지
│   ├── views/              # 화면 (페이지)
│   │   ├── home_view.py
│   │   ├── corporations_view.py
│   │   ├── detail_view.py
│   │   ├── analytics_view.py
│   │   ├── compare_view.py
│   │   └── settings_view.py
│   ├── components/         # 재사용 UI 컴포넌트
│   │   ├── navigation.py
│   │   ├── search_bar.py
│   │   ├── corporation_card.py
│   │   ├── financial_table.py
│   │   ├── chart_components.py
│   │   └── sync_progress.py
│   ├── services/           # 비즈니스 로직
│   │   ├── dart_service.py
│   │   ├── corporation_service.py
│   │   ├── financial_service.py
│   │   ├── analysis_service.py
│   │   ├── compare_service.py
│   │   └── sync_service.py
│   ├── models/             # 데이터베이스 모델
│   │   ├── database.py
│   │   ├── corporation.py
│   │   ├── filing.py
│   │   └── financial_statement.py
│   └── utils/              # 유틸리티
│       ├── formatters.py
│       ├── cache.py
│       └── errors.py
├── tests/                  # 테스트
│   ├── conftest.py
│   ├── unit/
│   └── integration/
└── docs/
    └── plans/              # 구현 계획서
```

## 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v

# 커버리지 포함
pytest tests/ -v --cov=src

# 특정 테스트 파일
pytest tests/unit/test_financial_service.py -v
```

## 코드 품질

```bash
# 린팅
ruff check src/

# 포맷팅 검사
black --check src/

# 타입 검사
mypy src/
```

## 플랫폼 호환성

| 기능 | Windows | macOS | Linux | Web |
|------|---------|-------|-------|-----|
| 핵심 UI | ✅ | ✅ | ✅ | ✅ |
| SQLite DB | ✅ | ✅ | ✅ | ⚠️ IndexedDB |
| DART API | ✅ | ✅ | ✅ | ⚠️ CORS |
| 파일 내보내기 | ✅ | ✅ | ✅ | ⚠️ 다운로드 |
| 차트 시각화 | ✅ | ✅ | ✅ | ✅ |

✅ 완전 지원 | ⚠️ 제한적 | ❌ 미지원

## 라이선스

MIT License

## 참고 자료

- [Flet 공식 문서](https://docs.flet.dev/)
- [DART Open API](https://opendart.fss.or.kr/)
- [dart-fss 라이브러리](https://github.com/josw123/dart-fss)

## 문제 해결

### 일반적인 문제

**Q: DART API 연결 오류가 발생합니다.**
A: API 키가 올바르게 설정되었는지 확인하세요. 환경변수 `DART_API_KEY` 또는 앱 설정에서 API 키를 입력하세요.

**Q: 데이터베이스 오류가 발생합니다.**
A: `~/.dart-db-flet/data/` 디렉토리의 권한을 확인하거나, 해당 폴더를 삭제 후 앱을 재시작하세요.

**Q: 빌드가 실패합니다.**
A: Flutter SDK가 올바르게 설치되었는지 확인하세요. `flet doctor` 명령으로 환경을 점검할 수 있습니다.

### 개발 관련

- 이슈 리포트: [GitHub Issues](https://github.com/gmdjlee/dart-db-flet/issues)
- 기여 가이드: CONTRIBUTING.md (예정)
