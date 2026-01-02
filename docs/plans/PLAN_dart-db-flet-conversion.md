# Implementation Plan: DART-DB Flet Standalone 전환

**Status**: 🔄 In Progress
**Started**: 2026-01-02
**Last Updated**: 2026-01-02 (Phase 1 completed)
**Estimated Completion**: 2026-01-20

**Framework**: Flet 0.8+
**Target Platforms**: Desktop (Windows/macOS/Linux) | Web
**Source Project**: https://github.com/gmdjlee/dart-db

---

**⚠️ CRITICAL INSTRUCTIONS**: After completing each phase:
1. ✅ Check off completed task checkboxes
2. 🧪 Run all quality gate validation commands
3. 🔄 Test on all target platforms: `flet run`, `flet run --web`
4. ⚠️ Verify ALL quality gate items pass
5. 📅 Update "Last Updated" date above
6. 📝 Document learnings in Notes section
7. ➡️ Only then proceed to next phase

⛔ **DO NOT skip quality gates or proceed with failing checks**

---

## 📋 Overview

### Feature Description
한국 상장기업(KOSPI/KOSDAQ)의 DART 전자공시 데이터를 수집, 분석, 시각화하는 **Docker/API 없이 동작하는 Standalone 크로스플랫폼 데스크톱 애플리케이션**으로 전환합니다.

### 전환 목표
- Docker, PostgreSQL, Redis 설치 불필요
- 단일 실행 파일 배포 (Windows .exe, macOS .app)
- 로컬 SQLite 데이터베이스
- Python Flet UI로 Next.js 대시보드 대체

### Success Criteria
- [ ] Windows에서 standalone .exe로 실행 가능
- [ ] 기업 검색 및 목록 조회 기능 동작
- [ ] 재무제표 조회 및 분석 기능 동작
- [ ] 차트 시각화 (재무비율, 성장률) 동작
- [ ] 기업 비교 기능 동작
- [ ] DART API 연동 및 데이터 수집 동작
- [ ] 모든 테스트 통과 (pytest)
- [ ] Works correctly on all target platforms

### User Impact
- 복잡한 서버 설정 없이 즉시 사용 가능
- 오프라인에서도 수집된 데이터 조회 가능
- 가벼운 설치 및 빠른 실행

### Platform Compatibility Matrix

| Feature Aspect | Windows | macOS | Linux | Web |
|---------------|---------|-------|-------|-----|
| Core UI | ✅ | ✅ | ✅ | ✅ |
| SQLite Database | ✅ | ✅ | ✅ | ⚠️ IndexedDB |
| DART API 연동 | ✅ | ✅ | ✅ | ⚠️ CORS |
| 파일 내보내기 | ✅ | ✅ | ✅ | ⚠️ 다운로드 |
| 차트 시각화 | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ Full Support | ⚠️ Limited | ❌ Not Available

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| PostgreSQL → SQLite | 단일 파일 DB, 설치 불필요 | 동시성 제한, 대용량 시 성능 |
| FastAPI → 직접 호출 | API 레이어 불필요, 단순화 | 웹 API 제공 불가 |
| Next.js → Flet UI | Python 단일 언어, 크로스플랫폼 | React 생태계 사용 불가 |
| Redis → dict/diskcache | 로컬 캐시로 충분 | 분산 캐시 불가 |
| Celery → asyncio | 단일 프로세스 비동기 | 분산 처리 불가 |
| Clean Architecture 유지 | 기존 로직 재사용 극대화 | 초기 구조 설정 복잡 |

### Flet Control Architecture
```
📁 dart-db-flet/
├── 📄 pyproject.toml
├── 📄 README.md
├── 📁 src/
│   ├── 📄 main.py                    # Flet 앱 진입점
│   ├── 📁 assets/
│   │   ├── 📄 icon.png
│   │   └── 📄 splash.png
│   ├── 📁 views/                     # 화면 (페이지)
│   │   ├── 📄 __init__.py
│   │   ├── 📄 home_view.py           # 대시보드 홈
│   │   ├── 📄 corporations_view.py   # 기업 목록
│   │   ├── 📄 detail_view.py         # 기업 상세/재무제표
│   │   ├── 📄 analytics_view.py      # 분석 도구
│   │   ├── 📄 compare_view.py        # 기업 비교
│   │   └── 📄 settings_view.py       # 설정
│   ├── 📁 components/                # 재사용 UI 컴포넌트
│   │   ├── 📄 __init__.py
│   │   ├── 📄 corporation_card.py
│   │   ├── 📄 financial_table.py
│   │   ├── 📄 chart_components.py
│   │   ├── 📄 search_bar.py
│   │   └── 📄 navigation.py
│   ├── 📁 services/                  # 비즈니스 로직
│   │   ├── 📄 __init__.py
│   │   ├── 📄 dart_service.py        # DART API 연동
│   │   ├── 📄 corporation_service.py
│   │   ├── 📄 financial_service.py
│   │   └── 📄 analysis_service.py
│   ├── 📁 models/                    # SQLite 모델
│   │   ├── 📄 __init__.py
│   │   ├── 📄 database.py
│   │   ├── 📄 corporation.py
│   │   ├── 📄 filing.py
│   │   └── 📄 financial_statement.py
│   └── 📁 utils/
│       ├── 📄 __init__.py
│       ├── 📄 formatters.py
│       ├── 📄 constants.py
│       └── 📄 cache.py
├── 📁 tests/
│   ├── 📄 conftest.py
│   ├── 📁 unit/
│   ├── 📁 integration/
│   └── 📁 e2e/
└── 📁 docs/
    └── 📁 plans/
```

---

## 📦 Dependencies

### Required Before Starting
- [ ] Python 3.11+ installed
- [ ] Flet 0.8+ installed: `pip install "flet>=0.25.0"`
- [ ] Development tools: `pip install pytest pytest-cov pytest-asyncio black ruff mypy`
- [ ] Project structure initialized

### External Dependencies
```toml
# pyproject.toml dependencies
[project]
dependencies = [
    "flet>=0.25.0",
    "dart-fss>=0.4.15",
    "sqlalchemy>=2.0.25",
    "aiosqlite>=0.19.0",
    "pandas>=2.2.0",
    "openpyxl>=3.1.2",
    "httpx>=0.26.0",
    "python-dotenv>=1.0.1",
    "diskcache>=5.6.0",
]
```

### dart-db에서 제외되는 패키지
```
# 제외 (Standalone에 불필요)
- fastapi, uvicorn (API 서버)
- celery, redis, aioredis (분산 작업)
- psycopg2-binary (PostgreSQL)
- pgvector (벡터 검색)
- arelle-release (무거움, 선택적)
- sentence-transformers (AI 모델)
- prometheus-client (모니터링)
```

### Platform-Specific Requirements
- [ ] **Windows Build**: PyInstaller 또는 Flet build
- [ ] **macOS Build**: Flet build (Apple Silicon 지원)
- [ ] **Linux Build**: Flet build
- [ ] **Web Build**: Flet build web (CORS 제한 있음)

---

## 🧪 Test Strategy

### Testing Approach
**TDD Principle**: Write tests FIRST, then implement to make them pass

### Test Pyramid for This Feature
| Test Type | Coverage Target | Purpose |
|-----------|-----------------|---------|
| **Unit Tests** | ≥80% | Services, models, utilities |
| **Integration Tests** | Critical paths | DB operations, DART API |
| **E2E Tests** | Key user flows | Full UI flow validation (manual) |

### Test File Organization
```
tests/
├── conftest.py                    # Shared fixtures, mock page
├── unit/
│   ├── test_corporation_service.py
│   ├── test_financial_service.py
│   ├── test_analysis_service.py
│   └── test_formatters.py
├── integration/
│   ├── test_database.py
│   ├── test_dart_api.py
│   └── test_views.py
└── e2e/
    └── test_app_flow.py
```

### pytest Configuration
```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock, AsyncMock
import flet as ft
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def mock_page():
    """Create a mock Flet Page for testing."""
    page = MagicMock(spec=ft.Page)
    page.platform = ft.PagePlatform.WINDOWS
    page.width = 1200
    page.height = 800
    page.update = MagicMock()
    return page

@pytest.fixture
def test_db():
    """Create in-memory SQLite for testing."""
    from src.models.database import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

@pytest.fixture
def mock_dart_api():
    """Mock DART API responses."""
    mock = AsyncMock()
    mock.get_corporation_list.return_value = [
        {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930"}
    ]
    return mock
```

---

## 🚀 Implementation Phases

### Phase 1: 프로젝트 기반 구조 설정
**Goal**: Flet 프로젝트 초기화, SQLite 모델 정의, 기본 네비게이션
**Estimated Time**: 4 hours
**Status**: ✅ Completed

#### Tasks

**🔴 RED: Write Failing Tests First**
- [x] **Test 1.1**: SQLite 데이터베이스 연결 테스트
  - File: `tests/unit/test_database.py`
  - Test cases:
    ```python
    class TestDatabase:
        def test_create_tables(self, test_db):
            # Tables should be created
            assert 'corporations' in test_db.get_bind().table_names()

        def test_corporation_crud(self, test_db):
            # Basic CRUD operations
            pass
    ```

- [x] **Test 1.2**: 기본 앱 구조 테스트
  - File: `tests/integration/test_app_structure.py`
  - Test cases: 앱 초기화, 네비게이션 설정

**🟢 GREEN: Implement to Make Tests Pass**
- [x] **Task 1.3**: pyproject.toml 및 프로젝트 구조 생성
  - Files: `pyproject.toml`, `src/__init__.py`, 디렉토리 구조

- [x] **Task 1.4**: SQLite 모델 정의 (SQLAlchemy)
  - Files: `src/models/database.py`, `src/models/corporation.py`, `src/models/filing.py`, `src/models/financial_statement.py`
  - dart-db의 모델을 SQLite 호환으로 변환

- [x] **Task 1.5**: Flet 앱 기본 구조 및 네비게이션
  - Files: `src/main.py`, `src/components/navigation.py`
  - NavigationRail 또는 NavigationBar 기반

**🔵 REFACTOR: Clean Up Code**
- [x] **Task 1.6**: 코드 정리 및 타입 힌트 추가

#### Quality Gate ✋

**TDD Compliance**:
- [x] Tests written FIRST and initially failed
- [x] Production code written to make tests pass
- [x] Test coverage ≥80% for models (89% achieved)

**Build & Run**:
- [x] `flet run src/main.py` 실행 성공
- [x] `pytest tests/unit/test_database.py -v` 통과
- [x] 네비게이션 기본 동작 확인

**Validation Commands**:
```bash
pytest tests/ -v --cov=src
ruff check src/
black --check src/
flet run src/main.py
```

---

### Phase 2: DART 서비스 및 기업 데이터 연동
**Goal**: dart-fss 연동, 기업 목록 수집/저장, 기본 기업 검색
**Estimated Time**: 4 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**
- [ ] **Test 2.1**: DART 서비스 테스트
  - File: `tests/unit/test_dart_service.py`
  - Test cases:
    ```python
    class TestDartService:
        @pytest.mark.asyncio
        async def test_get_corporation_list(self, mock_dart_api):
            service = DartService(api=mock_dart_api)
            corps = await service.get_corporation_list()
            assert len(corps) > 0

        def test_api_key_required(self):
            with pytest.raises(ValueError):
                DartService(api_key=None)
    ```

- [ ] **Test 2.2**: Corporation 서비스 테스트
  - File: `tests/unit/test_corporation_service.py`
  - Test cases: 검색, 필터링, 페이지네이션

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 2.3**: DART 서비스 구현
  - File: `src/services/dart_service.py`
  - dart-fss 라이브러리 래핑

- [ ] **Task 2.4**: Corporation 서비스 구현
  - File: `src/services/corporation_service.py`
  - 기업 검색, 목록 조회

- [ ] **Task 2.5**: 데이터 동기화 로직
  - File: `src/services/sync_service.py`
  - DART → SQLite 동기화

**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 2.6**: 캐싱 적용 (diskcache)
- [ ] **Task 2.7**: 에러 핸들링 강화

#### Quality Gate ✋

**Build & Tests**:
- [ ] DART API 연결 테스트 (mock)
- [ ] 기업 데이터 CRUD 동작
- [ ] `pytest tests/unit/test_dart_service.py -v` 통과

---

### Phase 3: 기업 목록/검색 UI
**Goal**: 기업 목록 화면, 검색 기능, 자동완성
**Estimated Time**: 4 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**
- [ ] **Test 3.1**: CorporationsView 테스트
  - File: `tests/integration/test_corporations_view.py`
  - Test cases:
    ```python
    class TestCorporationsView:
        def test_search_filters_list(self, mock_page):
            view = CorporationsView(mock_page)
            view.search_field.value = "삼성"
            view._on_search(None)
            # Assert filtered results

        def test_pagination_works(self, mock_page):
            view = CorporationsView(mock_page)
            view._next_page(None)
            assert view.current_page == 2
    ```

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 3.2**: SearchBar 컴포넌트
  - File: `src/components/search_bar.py`
  - 자동완성, 최근 검색어

- [ ] **Task 3.3**: CorporationCard 컴포넌트
  - File: `src/components/corporation_card.py`
  - 기업 정보 카드 UI

- [ ] **Task 3.4**: CorporationsView 구현
  - File: `src/views/corporations_view.py`
  - ListView + 검색 + 필터 + 페이지네이션

**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 3.5**: 반응형 레이아웃 (ResponsiveRow)
- [ ] **Task 3.6**: 로딩 상태 표시

#### Quality Gate ✋

**UI/UX Quality**:
- [ ] 검색 결과 0.5초 내 표시
- [ ] 스크롤 부드러움
- [ ] 반응형 레이아웃 동작

**Platform Testing**:
- [ ] Desktop: `flet run src/main.py` ✅
- [ ] Web: `flet run --web src/main.py` ✅

---

### Phase 4: 기업 상세 및 재무제표 화면
**Goal**: 기업 상세 정보, 재무제표 테이블, 기본 지표
**Estimated Time**: 4 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**
- [ ] **Test 4.1**: Financial 서비스 테스트
  - File: `tests/unit/test_financial_service.py`
  - Test cases: 재무제표 조회, 비율 계산

- [ ] **Test 4.2**: DetailView 테스트
  - File: `tests/integration/test_detail_view.py`

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 4.3**: Financial 서비스 구현
  - File: `src/services/financial_service.py`
  - dart-db의 로직 이식

- [ ] **Task 4.4**: FinancialTable 컴포넌트
  - File: `src/components/financial_table.py`
  - DataTable 기반 재무제표

- [ ] **Task 4.5**: DetailView 구현
  - File: `src/views/detail_view.py`
  - 탭: 기본정보, 재무제표, 재무비율

**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 4.6**: 숫자 포맷팅 (억원, %)
- [ ] **Task 4.7**: 연도별 비교 표시

#### Quality Gate ✋

**Functionality**:
- [ ] 재무제표 3개년 데이터 표시
- [ ] 재무비율 계산 정확성 검증
- [ ] 탭 전환 동작

---

### Phase 5: 차트 및 분석 기능
**Goal**: 재무 차트 (Line, Bar), 성장률 분석, 트렌드
**Estimated Time**: 4 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**
- [ ] **Test 5.1**: Analysis 서비스 테스트
  - File: `tests/unit/test_analysis_service.py`
  - Test cases: CAGR 계산, 재무비율 계산

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 5.2**: Analysis 서비스 구현
  - File: `src/services/analysis_service.py`
  - 성장률, CAGR, 재무비율

- [ ] **Task 5.3**: ChartComponents 구현
  - File: `src/components/chart_components.py`
  - LineChart, BarChart 래퍼

- [ ] **Task 5.4**: AnalyticsView 구현
  - File: `src/views/analytics_view.py`
  - 분석 도구 화면

**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 5.5**: 차트 애니메이션
- [ ] **Task 5.6**: 범례 및 툴팁

#### Quality Gate ✋

**Visualization**:
- [ ] 매출액/영업이익 추이 차트
- [ ] 재무비율 비교 차트
- [ ] 반응형 차트 크기

---

### Phase 6: 기업 비교 기능
**Goal**: 최대 5개 기업 선택 비교, 레이더 차트
**Estimated Time**: 3 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**
- [ ] **Test 6.1**: 기업 비교 로직 테스트
  - File: `tests/unit/test_compare_service.py`

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 6.2**: CompareView 구현
  - File: `src/views/compare_view.py`
  - 기업 선택, 비교 테이블, 차트

- [ ] **Task 6.3**: 비교 차트 컴포넌트
  - 레이더 차트 또는 그룹 바 차트

**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 6.4**: 비교 기업 저장/불러오기

#### Quality Gate ✋

**Functionality**:
- [ ] 최대 5개 기업 동시 비교
- [ ] 주요 지표 비교 테이블
- [ ] 시각적 비교 차트

---

### Phase 7: 데이터 수집 및 동기화
**Goal**: DART 데이터 수집 UI, 진행률 표시, 백그라운드 동기화
**Estimated Time**: 4 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**
- [ ] **Test 7.1**: 동기화 서비스 테스트
  - File: `tests/unit/test_sync_service.py`

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 7.2**: 동기화 서비스 강화
  - File: `src/services/sync_service.py`
  - Rate Limiting, 재시도 로직

- [ ] **Task 7.3**: SettingsView 구현
  - File: `src/views/settings_view.py`
  - API 키 설정, 동기화 트리거

- [ ] **Task 7.4**: 진행률 표시 컴포넌트
  - ProgressBar, 상태 메시지

**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 7.5**: 에러 복구 로직
- [ ] **Task 7.6**: 로그 저장

#### Quality Gate ✋

**Data Collection**:
- [ ] 기업 목록 수집 동작
- [ ] 재무제표 수집 동작
- [ ] 진행률 실시간 표시

---

### Phase 8: 빌드 및 배포
**Goal**: Windows/macOS 빌드, 최종 테스트
**Estimated Time**: 3 hours
**Status**: ⏳ Pending

#### Tasks

- [ ] **Task 8.1**: pyproject.toml 빌드 설정 완성
- [ ] **Task 8.2**: Windows 빌드 테스트
  ```bash
  flet build windows
  ```
- [ ] **Task 8.3**: macOS 빌드 테스트
  ```bash
  flet build macos
  ```
- [ ] **Task 8.4**: 빌드된 앱 기능 테스트
- [ ] **Task 8.5**: README 및 사용자 가이드 작성

#### Build Quality Gate ✋
- [ ] Windows .exe 실행 성공
- [ ] macOS .app 실행 성공
- [ ] 모든 핵심 기능 동작 확인
- [ ] 앱 아이콘 표시

---

## ⚠️ Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| dart-fss 모바일 미지원 | Low | Medium | Desktop 전용으로 제한 |
| 대용량 데이터 성능 | Medium | Medium | 페이지네이션, 가상 스크롤 |
| DART API Rate Limit | Medium | High | 로컬 캐싱, 지수 백오프 |
| SQLite 동시성 | Low | Low | WAL 모드 사용 |
| Flet 차트 제한 | Low | Medium | 커스텀 차트 또는 외부 라이브러리 |

### Flet-Specific Risks
- [ ] **Binary Packages**: dart-fss, pandas는 Desktop에서 정상 동작
- [ ] **Platform APIs**: 파일 시스템 접근 정상
- [ ] **Responsive UI**: 다양한 윈도우 크기 테스트

---

## 🔄 Rollback Strategy

### If Phase 1 Fails
```bash
git reset --hard HEAD~n
```
- 프로젝트 구조 재설정 필요
- pyproject.toml 수정

### If Phase 2-7 Fails
- 이전 Phase 완료 상태로 복귀
- 해당 Phase의 tests/, src/ 변경 사항 되돌리기

---

## 📊 Progress Tracking

### Completion Status
- **Phase 1 (프로젝트 기반)**: ✅ 100%
- **Phase 2 (DART 연동)**: ⏳ 0%
- **Phase 3 (기업 목록 UI)**: ⏳ 0%
- **Phase 4 (기업 상세)**: ⏳ 0%
- **Phase 5 (차트/분석)**: ⏳ 0%
- **Phase 6 (기업 비교)**: ⏳ 0%
- **Phase 7 (데이터 수집)**: ⏳ 0%
- **Phase 8 (빌드/배포)**: ⏳ 0%

**Overall Progress**: 12.5% complete (1/8 phases)

### Time Tracking
| Phase | Estimated | Actual | Variance |
|-------|-----------|--------|----------|
| Phase 1 | 4 hours | ~2 hours | -2 hours |
| Phase 2 | 4 hours | - | - |
| Phase 3 | 4 hours | - | - |
| Phase 4 | 4 hours | - | - |
| Phase 5 | 4 hours | - | - |
| Phase 6 | 3 hours | - | - |
| Phase 7 | 4 hours | - | - |
| Phase 8 | 3 hours | - | - |
| **Total** | 30 hours | - | - |

### Platform Testing Status
| Platform | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 | Phase 7 | Phase 8 |
|----------|---------|---------|---------|---------|---------|---------|---------|---------|
| Windows | ✅ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| macOS | ✅ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| Web | ✅ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |

---

## 📝 Notes & Learnings

### Implementation Notes
- dart-db의 Clean Architecture 구조를 최대한 유지하여 서비스 레이어 재사용
- PostgreSQL 모델을 SQLite 호환으로 변환 시 pgvector, TimescaleDB 기능 제거 필요

### dart-db에서 재사용할 코드
- `src/domain/` - 엔티티, 값 객체 (수정 없이 사용)
- `src/application/usecases/` - 유스케이스 로직 (DB 연결만 변경)
- `src/collector/` - DART API 클라이언트 (그대로 사용)
- `src/normalizer/` - 계정과목 표준화 (그대로 사용)

### Flet Tips Learned
- SQLAlchemy BigInteger는 SQLite에서 autoincrement가 제대로 동작하지 않음 → Integer 사용 권장
- Flet Page mock 테스트 시 `window` 속성도 MagicMock으로 설정 필요
- Python 3.11+에서 `Optional[X]` 대신 `X | None` 사용 권장 (ruff UP045)
- `typing.Dict` 대신 `dict` 사용 권장 (ruff UP006)

---

## 📚 References

### Flet Documentation
- [Flet Docs](https://docs.flet.dev/)
- [API Reference](https://docs.flet.dev/api-reference/)
- [Cookbook](https://docs.flet.dev/cookbook/)
- [Publishing Guide](https://docs.flet.dev/publish/)

### dart-db 원본
- [GitHub Repository](https://github.com/gmdjlee/dart-db)
- [DART Open API](https://opendart.fss.or.kr/)

---

## ✅ Final Checklist

**Before marking plan as COMPLETE**:
- [ ] All phases completed with quality gates passed
- [ ] Full integration testing performed
- [ ] Documentation updated
- [ ] Windows build tested
- [ ] macOS build tested (if available)
- [ ] Performance acceptable
- [ ] All stakeholders notified
- [ ] Plan document archived for future reference

---

**Plan Status**: 🔄 In Progress
**Next Action**: Phase 2 시작 - DART 서비스 및 기업 데이터 연동
**Blocked By**: None
