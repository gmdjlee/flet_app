"""Detail View - Corporation details and financial statements."""

import flet as ft
from sqlalchemy.orm import Session

from src.components.financial_table import (
    FinancialSummaryCard,
    FinancialTable,
    RatioIndicator,
)
from src.models.corporation import Corporation
from src.models.database import get_engine, get_session
from src.models.financial_statement import FinancialStatement
from src.services.corporation_service import CorporationService
from src.services.financial_service import FinancialService
from src.utils.formatters import (
    format_date,
    format_growth,
    get_growth_color,
    get_ratio_status,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class DetailView(ft.View):
    """Detail view for displaying corporation information and financials.

    Shows corporation details, financial statements, and financial ratios
    in a tabbed interface.

    Attributes:
        corp_code: DART corporation code.
        corporation: Loaded Corporation instance.
        financial_statements: List of financial statements.
        selected_year: Currently selected business year.
        available_years: List of years with data.
        is_loading: Loading state flag.
    """

    def __init__(
        self,
        page: ft.Page,
        corp_code: str,
        session: Session | None = None,
    ) -> None:
        """Initialize DetailView.

        Args:
            page: Flet page instance.
            corp_code: DART corporation code to display.
            session: Database session (optional).
        """
        self._page_ref = page
        self.corp_code = corp_code
        self._session = session

        # Data
        self.corporation: Corporation | None = None
        self.financial_statements: list[FinancialStatement] = []
        self.available_years: list[str] = []
        self.selected_year: str = ""

        # Loading state
        self.is_loading = False
        self.loading_indicator = ft.ProgressRing(
            width=30,
            height=30,
            stroke_width=3,
            visible=False,
        )

        # Tab state
        self.selected_tab_index = 0

        # Tab buttons - using TabBar for Flet 1.0+ compatibility
        self.tab_buttons = ft.TabBar(
            selected_index=0,
            tabs=[
                ft.Tab(label="기본 정보", icon=ft.Icons.INFO_OUTLINED),
                ft.Tab(label="재무제표", icon=ft.Icons.TABLE_CHART),
                ft.Tab(label="재무비율", icon=ft.Icons.PIE_CHART),
            ],
            on_change=self._on_tab_change,
        )
        self.tabs = self.tab_buttons
        self.tab_bar = self.tab_buttons

        # Tab content container
        self.tab_content = ft.Container(expand=True)

        # Year selector
        self.year_dropdown = ft.Dropdown(
            label="사업연도",
            width=150,
            on_select=self._on_year_change,
        )

        # Build view
        super().__init__(
            route=f"/detail/{corp_code}",
            controls=[self._build()],
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        # Load data
        self._load_data()

    @property
    def session(self) -> Session:
        """Get or create database session."""
        if self._session is None:
            engine = get_engine()
            self._session = get_session(engine)
        return self._session

    def _build(self) -> ft.Control:
        """Build the detail view.

        Returns:
            Main container with all content.
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header with back button
                    self._build_header(),
                    ft.Divider(),
                    # Tab bar (SegmentedButton)
                    ft.Container(
                        content=self.tab_buttons,
                        padding=ft.Padding(left=0, right=0, top=10, bottom=10),
                    ),
                    # Tab content
                    self.tab_content,
                ],
                expand=True,
            ),
            padding=20,
            expand=True,
        )

    def _build_header(self) -> ft.Control:
        """Build header with navigation and title.

        Returns:
            Header row.
        """
        self.back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="목록으로",
            on_click=self._go_back,
        )

        self.title_text = ft.Text(
            "기업 상세",
            size=24,
            weight=ft.FontWeight.BOLD,
        )

        self.subtitle_text = ft.Text(
            "",
            size=14,
            color=ft.Colors.GREY_600,
        )

        return ft.Row(
            controls=[
                self.back_button,
                ft.Container(width=10),
                ft.Column(
                    controls=[
                        self.title_text,
                        self.subtitle_text,
                    ],
                    spacing=2,
                ),
                ft.Container(expand=True),
                self.loading_indicator,
            ],
        )

    def _build_basic_info_tab(self) -> ft.Control:
        """Build basic information tab content.

        Returns:
            Basic info container.
        """
        if self.corporation is None:
            return self._build_not_found()

        corp = self.corporation

        # Info cards
        info_items = [
            ("회사명", corp.corp_name),
            ("영문명", corp.corp_name_eng or "-"),
            ("종목코드", corp.stock_code or "-"),
            ("시장구분", corp.market_display),
            ("대표이사", corp.ceo_nm or "-"),
            ("설립일", format_date(corp.est_dt)),
            ("주소", corp.adres or "-"),
            ("홈페이지", corp.hm_url or "-"),
            ("전화번호", corp.phn_no or "-"),
            ("결산월", f"{corp.acc_mt}월" if corp.acc_mt else "-"),
        ]

        info_rows = []
        for i in range(0, len(info_items), 2):
            row_items = []
            for j in range(2):
                if i + j < len(info_items):
                    label, value = info_items[i + j]
                    row_items.append(
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        label,
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                    ft.Text(
                                        value,
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                                spacing=2,
                            ),
                            padding=15,
                            border=ft.border.all(1, ft.Colors.GREY_200),
                            border_radius=8,
                            expand=True,
                            col={"xs": 12, "sm": 6, "md": 6},
                        )
                    )
            info_rows.append(
                ft.ResponsiveRow(
                    controls=row_items,
                    spacing=10,
                    run_spacing=10,
                )
            )

        # Financial summary cards
        summary = self._get_financial_summary()
        summary_cards = []

        if summary:
            summary_cards = [
                ft.Container(height=20),
                ft.Text("주요 재무지표", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(
                            content=FinancialSummaryCard(
                                title="자산총계",
                                value=summary.get("total_assets"),
                                icon=ft.Icons.ACCOUNT_BALANCE,
                                change=self._get_yoy("자산총계"),
                            ),
                            col={"xs": 12, "sm": 6, "md": 4},
                        ),
                        ft.Container(
                            content=FinancialSummaryCard(
                                title="매출액",
                                value=summary.get("revenue"),
                                icon=ft.Icons.TRENDING_UP,
                                change=self._get_yoy("매출액"),
                            ),
                            col={"xs": 12, "sm": 6, "md": 4},
                        ),
                        ft.Container(
                            content=FinancialSummaryCard(
                                title="영업이익",
                                value=summary.get("operating_income"),
                                icon=ft.Icons.MONETIZATION_ON,
                                change=self._get_yoy("영업이익"),
                            ),
                            col={"xs": 12, "sm": 6, "md": 4},
                        ),
                    ],
                    spacing=10,
                    run_spacing=10,
                ),
            ]

        return ft.Column(
            controls=[
                *info_rows,
                *summary_cards,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=10,
        )

    def _build_financial_tab(self) -> ft.Control:
        """Build financial statements tab content.

        Returns:
            Financial statements container.
        """
        if self.corporation is None:
            return self._build_not_found()

        if not self.available_years:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.FOLDER_OFF_OUTLINED,
                            size=48,
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Text(
                            "재무제표 데이터가 없습니다",
                            color=ft.Colors.GREY_500,
                        ),
                        ft.Text(
                            "설정에서 DART API를 통해 데이터를 동기화하세요",
                            size=12,
                            color=ft.Colors.GREY_400,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True,
                padding=50,
            )

        # Statement type selector - using Dropdown for Flet 0.70+ compatibility
        self.statement_type_buttons = ft.Dropdown(
            label="재무제표 유형",
            value="BS",
            width=180,
            options=[
                ft.dropdown.Option(key="BS", text="재무상태표"),
                ft.dropdown.Option(key="IS", text="손익계산서"),
            ],
            on_select=self._on_statement_type_change,
        )

        # Get statements for current view
        self.bs_table = FinancialTable(
            statements=self._get_balance_sheet(),
            show_yoy=True,
        )
        self.is_table = FinancialTable(
            statements=self._get_income_statement(),
            show_yoy=True,
        )

        self.statement_content = ft.Container(
            content=self.bs_table,
            expand=True,
        )

        return ft.Column(
            controls=[
                # Year selector row
                ft.Row(
                    controls=[
                        self.year_dropdown,
                        ft.Container(expand=True),
                        ft.Text(
                            "단위: 원 (YoY: 전년대비)",
                            size=12,
                            color=ft.Colors.GREY_500,
                        ),
                    ],
                ),
                ft.Container(height=10),
                self.statement_type_buttons,
                ft.Container(height=10),
                self.statement_content,
            ],
            expand=True,
        )

    def _build_ratios_tab(self) -> ft.Control:
        """Build financial ratios tab content.

        Returns:
            Ratios container.
        """
        if self.corporation is None:
            return self._build_not_found()

        ratios = self.get_financial_ratios()

        if not ratios or all(v is None for v in ratios.values()):
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.ANALYTICS_OUTLINED,
                            size=48,
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Text(
                            "재무비율 데이터가 없습니다",
                            color=ft.Colors.GREY_500,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True,
                padding=50,
            )

        # Ratio display names
        ratio_names = {
            "debt_ratio": "부채비율",
            "current_ratio": "유동비율",
            "operating_margin": "영업이익률",
            "net_margin": "순이익률",
            "roe": "ROE (자기자본이익률)",
            "roa": "ROA (총자산이익률)",
        }

        ratio_indicators = []
        for key, name in ratio_names.items():
            value = ratios.get(key)
            status, color = get_ratio_status(key, value)
            ratio_indicators.append(
                ft.Container(
                    content=RatioIndicator(
                        name=name,
                        value=value,
                        status=status,
                        status_color=color,
                    ),
                    col={"xs": 12, "sm": 6, "md": 4},
                )
            )

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.year_dropdown,
                        ft.Container(expand=True),
                    ],
                ),
                ft.Container(height=20),
                ft.Text(
                    "주요 재무비율",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(height=10),
                ft.ResponsiveRow(
                    controls=ratio_indicators,
                    spacing=10,
                    run_spacing=10,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_not_found(self) -> ft.Control:
        """Build not found state.

        Returns:
            Not found container.
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.ERROR_OUTLINE,
                        size=64,
                        color=ft.Colors.ORANGE_400,
                    ),
                    ft.Text(
                        "기업을 찾을 수 없습니다",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"코드: {self.corp_code}",
                        color=ft.Colors.GREY_500,
                    ),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "목록으로 돌아가기",
                        on_click=self._go_back,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            alignment=ft.alignment.Alignment(0, 0),
            expand=True,
        )

    def _load_data(self) -> None:
        """Load corporation and financial data."""
        self._set_loading(True)

        try:
            # Load corporation
            corp_service = CorporationService(self.session)
            self.corporation = corp_service.get_by_corp_code(self.corp_code)

            if self.corporation:
                # Update header
                self.title_text.value = self.corporation.corp_name
                self.subtitle_text.value = (
                    f"{self.corporation.stock_code or '-'} | " f"{self.corporation.market_display}"
                )

                # Load financial data
                fin_service = FinancialService(self.session)
                self.available_years = fin_service.get_available_years(self.corp_code)

                if self.available_years:
                    self.selected_year = self.available_years[0]

                    # Update year dropdown
                    self.year_dropdown.options = [
                        ft.dropdown.Option(year) for year in self.available_years
                    ]
                    self.year_dropdown.value = self.selected_year

                    # Load statements
                    self.financial_statements = fin_service.get_statements(
                        corp_code=self.corp_code,
                        bsns_year=self.selected_year,
                    )

        except Exception as e:
            print(f"Error loading data: {e}")
            self.corporation = None

        finally:
            self._set_loading(False)
            self._update_tab_content()

    def _set_loading(self, is_loading: bool) -> None:
        """Set loading state.

        Args:
            is_loading: Whether loading.
        """
        self.is_loading = is_loading
        self.loading_indicator.visible = is_loading
        try:
            self.loading_indicator.update()
        except Exception:
            pass

    def _update_tab_content(self) -> None:
        """Update the tab content based on selected tab."""
        if self.selected_tab_index == 0:
            self.tab_content.content = self._build_basic_info_tab()
        elif self.selected_tab_index == 1:
            self.tab_content.content = self._build_financial_tab()
        elif self.selected_tab_index == 2:
            self.tab_content.content = self._build_ratios_tab()

        if self._page_ref:
            try:
                self._page_ref.update()
            except Exception:
                pass

    def _on_tab_change(self, e: ft.ControlEvent) -> None:
        """Handle tab change.

        Args:
            e: Control event.
        """
        self.selected_tab_index = e.control.selected_index
        self._update_tab_content()

    def _on_year_change(self, e: ft.ControlEvent) -> None:
        """Handle year selection change.

        Args:
            e: Control event.
        """
        self.selected_year = e.control.value

        # Reload statements for new year
        fin_service = FinancialService(self.session)
        self.financial_statements = fin_service.get_statements(
            corp_code=self.corp_code,
            bsns_year=self.selected_year,
        )

        self._update_tab_content()

    def _on_statement_type_change(self, e: ft.ControlEvent) -> None:
        """Handle statement type change.

        Args:
            e: Control event.
        """
        stmt_type = e.control.value
        if stmt_type and hasattr(self, "statement_content"):
            if stmt_type == "BS":
                self.statement_content.content = self.bs_table
            else:
                self.statement_content.content = self.is_table

            if self._page_ref:
                try:
                    self._page_ref.update()
                except Exception:
                    pass

    def _go_back(self, e: ft.ControlEvent | None) -> None:
        """Navigate back to corporations list.

        Args:
            e: Control event.
        """
        if self._page_ref:
            self._page_ref.go("/corporations")

    def _get_balance_sheet(self) -> list[FinancialStatement]:
        """Get balance sheet items.

        Returns:
            List of BS statements.
        """
        return [s for s in self.financial_statements if s.sj_div == "BS"]

    def _get_income_statement(self) -> list[FinancialStatement]:
        """Get income statement items.

        Returns:
            List of IS statements.
        """
        return [s for s in self.financial_statements if s.sj_div == "IS"]

    def _get_financial_summary(self) -> dict | None:
        """Get financial summary for current year.

        Returns:
            Summary dictionary or None.
        """
        if not self.selected_year:
            return None

        fin_service = FinancialService(self.session)
        return fin_service.get_financial_summary(
            self.corp_code,
            self.selected_year,
        )

    def _get_yoy(self, account_nm: str) -> float | None:
        """Get year-over-year change for account.

        Args:
            account_nm: Account name.

        Returns:
            YoY change percentage.
        """
        if not self.selected_year:
            return None

        fin_service = FinancialService(self.session)
        return fin_service.calculate_yoy_growth(
            self.corp_code,
            self.selected_year,
            account_nm,
        )

    def get_financial_ratios(self) -> dict:
        """Get financial ratios for current year.

        Returns:
            Dictionary of ratios.
        """
        if not self.selected_year:
            return {}

        fin_service = FinancialService(self.session)
        return fin_service.get_financial_ratios(
            self.corp_code,
            self.selected_year,
        )

    def _build_yoy_indicator(self, value: float | None) -> ft.Control:
        """Build YoY change indicator.

        Args:
            value: Change value.

        Returns:
            Indicator control.
        """
        if value is None:
            return ft.Text("-", color=ft.Colors.GREY_400)

        color = get_growth_color(value)
        text = format_growth(value)

        icon = ft.Icons.ARROW_UPWARD if value >= 0 else ft.Icons.ARROW_DOWNWARD

        return ft.Row(
            controls=[
                ft.Icon(icon, size=14, color=color),
                ft.Text(text, color=color, weight=ft.FontWeight.W_500),
            ],
            spacing=2,
        )

    def _calculate_yoy_change(self, current: int | None, prior: int | None) -> float | None:
        """Calculate YoY change.

        Args:
            current: Current value.
            prior: Prior value.

        Returns:
            Change percentage.
        """
        if current is None or prior is None or prior == 0:
            return None
        return ((current - prior) / abs(prior)) * 100
