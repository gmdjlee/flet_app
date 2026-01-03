"""Formatting utilities for financial data display."""

from typing import Literal


def format_amount(
    amount: int | float | None,
    unit: Literal["억원", "만원", "원"] = "억원",
    show_unit: bool = False,
) -> str:
    """Format monetary amount with appropriate unit.

    Args:
        amount: Amount in KRW (원).
        unit: Display unit ("억원", "만원", or "원").
        show_unit: Whether to append unit to the result.

    Returns:
        Formatted amount string.
    """
    if amount is None:
        return "-"

    if unit == "억원":
        value = amount / 100_000_000
        formatted = f"{value:,.1f}"
    elif unit == "만원":
        value = amount / 10_000
        formatted = f"{value:,.0f}"
    else:  # 원
        formatted = f"{amount:,.0f}"

    if show_unit:
        return f"{formatted} {unit}"
    return formatted


def format_amount_short(amount: int | float | None) -> str:
    """Format amount with automatic unit selection (조/억/만).

    Args:
        amount: Amount in KRW.

    Returns:
        Formatted string with appropriate unit.
    """
    if amount is None:
        return "-"

    abs_amount = abs(amount)
    sign = "-" if amount < 0 else ""

    if abs_amount >= 1_000_000_000_000:  # 조 단위
        value = abs_amount / 1_000_000_000_000
        return f"{sign}{value:,.1f}조"
    elif abs_amount >= 100_000_000:  # 억 단위
        value = abs_amount / 100_000_000
        return f"{sign}{value:,.0f}억"
    elif abs_amount >= 10_000:  # 만 단위
        value = abs_amount / 10_000
        return f"{sign}{value:,.0f}만"
    else:
        return f"{sign}{abs_amount:,.0f}원"


def format_percentage(
    value: float | None,
    decimal_places: int = 2,
    show_sign: bool = False,
) -> str:
    """Format value as percentage.

    Args:
        value: Percentage value (e.g., 28.57 for 28.57%).
        decimal_places: Number of decimal places.
        show_sign: Whether to show + for positive values.

    Returns:
        Formatted percentage string.
    """
    if value is None:
        return "-"

    if show_sign and value > 0:
        return f"+{value:.{decimal_places}f}%"
    return f"{value:.{decimal_places}f}%"


def format_growth(
    value: float | None,
    decimal_places: int = 1,
) -> str:
    """Format growth rate with sign indicator.

    Args:
        value: Growth rate as percentage.
        decimal_places: Number of decimal places.

    Returns:
        Formatted growth string with + or - sign.
    """
    if value is None:
        return "-"

    if value > 0:
        return f"+{value:.{decimal_places}f}%"
    elif value < 0:
        return f"{value:.{decimal_places}f}%"
    else:
        return "0.0%"


def format_ratio(
    value: float | None,
    decimal_places: int = 2,
) -> str:
    """Format financial ratio.

    Args:
        value: Ratio value (e.g., 1.5 for 1.5x).
        decimal_places: Number of decimal places.

    Returns:
        Formatted ratio string.
    """
    if value is None:
        return "-"

    return f"{value:.{decimal_places}f}"


def format_date(date_str: str | None) -> str:
    """Format date string (YYYYMMDD) to readable format.

    Args:
        date_str: Date string in YYYYMMDD format.

    Returns:
        Formatted date string (YYYY.MM.DD).
    """
    if not date_str or len(date_str) != 8:
        return "-"

    try:
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        return f"{year}.{month}.{day}"
    except (IndexError, ValueError):
        return "-"


def format_corp_cls(corp_cls: str | None) -> str:
    """Format corporation class to market name.

    Args:
        corp_cls: Corporation class code (Y/K/N/E).

    Returns:
        Market name.
    """
    market_names = {
        "Y": "KOSPI",
        "K": "KOSDAQ",
        "N": "KONEX",
        "E": "기타",
    }
    return market_names.get(corp_cls or "", "기타")


def format_report_code(reprt_code: str | None) -> str:
    """Format report code to readable name.

    Args:
        reprt_code: Report code.

    Returns:
        Report name.
    """
    report_names = {
        "11011": "사업보고서",
        "11012": "반기보고서",
        "11013": "1분기보고서",
        "11014": "3분기보고서",
    }
    return report_names.get(reprt_code or "", "기타")


def format_statement_type(sj_div: str | None) -> str:
    """Format statement type code to readable name.

    Args:
        sj_div: Statement division code.

    Returns:
        Statement type name.
    """
    statement_names = {
        "BS": "재무상태표",
        "IS": "손익계산서",
        "CIS": "포괄손익계산서",
        "CF": "현금흐름표",
        "SCE": "자본변동표",
    }
    return statement_names.get(sj_div or "", sj_div or "기타")


def get_growth_color(value: float | None) -> str:
    """Get color for growth value display.

    Args:
        value: Growth rate.

    Returns:
        Color code string (green/red/grey).
    """
    if value is None:
        return "grey"
    if value > 0:
        return "green"
    elif value < 0:
        return "red"
    return "grey"


def get_ratio_status(
    ratio_name: str,
    value: float | None,
) -> tuple[str, str]:
    """Get status and color for financial ratio.

    Args:
        ratio_name: Name of the ratio.
        value: Ratio value.

    Returns:
        Tuple of (status text, color).
    """
    if value is None:
        return ("N/A", "grey")

    # Define thresholds for common ratios
    if ratio_name == "debt_ratio":  # 부채비율
        if value < 100:
            return ("양호", "green")
        elif value < 200:
            return ("보통", "orange")
        else:
            return ("주의", "red")
    elif ratio_name == "current_ratio":  # 유동비율
        if value >= 200:
            return ("양호", "green")
        elif value >= 100:
            return ("보통", "orange")
        else:
            return ("주의", "red")
    elif ratio_name == "operating_margin":  # 영업이익률
        if value >= 15:
            return ("양호", "green")
        elif value >= 5:
            return ("보통", "orange")
        else:
            return ("주의", "red")
    elif ratio_name == "net_margin":  # 순이익률
        if value >= 10:
            return ("양호", "green")
        elif value >= 3:
            return ("보통", "orange")
        else:
            return ("주의", "red")
    elif ratio_name == "roe":  # ROE
        if value >= 15:
            return ("양호", "green")
        elif value >= 8:
            return ("보통", "orange")
        else:
            return ("주의", "red")

    return ("", "grey")
