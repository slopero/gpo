from __future__ import annotations

import json
import re
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Optional

from pypdf import PdfReader
import requests


@dataclass
class PdfMetrics:
    period_label: str
    retail_turnover_bln: Optional[str] = None
    retail_trade_yoy_pct: Optional[str] = None
    cpi_yoy_pct: Optional[str] = None
    cpi_month_pct: Optional[str] = None
    unemployment_mln: Optional[str] = None
    unemployment_yoy_pct: Optional[str] = None
    industrial_yoy_pct: Optional[str] = None


@dataclass
class AutoSalesStats:
    source_url: str
    status: str
    total_sales: Optional[int] = None
    top_brands: Optional[list[tuple[str, int]]] = None
    details: Optional[str] = None


class ReportGenerator:
    BASE_DIR = Path(__file__).resolve().parent
    INFO_DIR = BASE_DIR / "info"
    AEB_INDEX_PATH = BASE_DIR / "aeb_rus_sales_data" / "aeb_rus_sales_index.json"
    AUTO_SALES_CACHE_PATH = INFO_DIR / "auto_sales_cache.json"
    AUTO_SALES_URL_TEMPLATE = "https://auto.vercity.ru/statistics/sales/europe/{year}/russia/{month:02d}-{month:02d}/"
    AUTO_SALES_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8",
    }
    ENABLE_ONLINE_AUTO_SALES_FALLBACK = False

    MONTH_NAMES = {
        1: "январе", 2: "феврале", 3: "марте", 4: "апреле",
        5: "мае", 6: "июне", 7: "июле", 8: "августе",
        9: "сентябре", 10: "октябре", 11: "ноябре", 12: "декабре",
    }

    MONTH_NAMES_GENITIVE = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
    }
    MONTH_NAMES_NOMINATIVE = {
        1: "январь", 2: "февраль", 3: "март", 4: "апрель",
        5: "май", 6: "июнь", 7: "июль", 8: "август",
        9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь",
    }
    MONTH_WORD_RE = {
        1: r"январ(?:ь|я|е)?|january",
        2: r"феврал(?:ь|я|е)?|february",
        3: r"март(?:а|е)?|march",
        4: r"апрел(?:ь|я|е)?|april",
        5: r"ма(?:й|я|е)|may",
        6: r"июн(?:ь|я|е)?|june",
        7: r"июл(?:ь|я|е)?|july",
        8: r"август(?:а|е)?|august",
        9: r"сентябр(?:ь|я|е)?|september",
        10: r"октябр(?:ь|я|е)?|october|octover",
        11: r"ноябр(?:ь|я|е)?|november",
        12: r"декабр(?:ь|я|е)?|december",
    }

    # Поддерживает имена вида:
    # osn-01-2026.pdf, Osn-09-2014_2.pdf, osn-08-2019(3).pdf
    PDF_NAME_RE = re.compile(
        r"^osn-(?P<month>\d{2})-(?P<year>\d{4})(?:[_\-\s]?\d+|\(\d+\))?\.pdf$",
        re.IGNORECASE,
    )

    _text_cache: dict[Path, str] = {}
    _aeb_rows_cache: Optional[list[dict]] = None

    @classmethod
    def get_month_name_prepositional(cls, month: int) -> str:
        return cls.MONTH_NAMES.get(month, "")

    @classmethod
    def get_month_name_genitive(cls, month: int) -> str:
        return cls.MONTH_NAMES_GENITIVE.get(month, "")

    @classmethod
    def get_month_name_nominative(cls, month: int) -> str:
        return cls.MONTH_NAMES_NOMINATIVE.get(month, "")

    @classmethod
    def _scan_periods(cls) -> list[tuple[int, int, Path]]:
        if not cls.INFO_DIR.exists():
            return []

        periods: list[tuple[int, int, Path]] = []
        for pdf_path in cls.INFO_DIR.glob("*.pdf"):
            match = cls.PDF_NAME_RE.match(pdf_path.name)
            if not match:
                continue
            month = int(match.group("month"))
            year = int(match.group("year"))
            if 1 <= month <= 12:
                periods.append((year, month, pdf_path))

        periods.sort(key=lambda item: (item[0], item[1]))
        return periods

    @classmethod
    def _load_auto_sales_cache(cls) -> dict:
        if not cls.AUTO_SALES_CACHE_PATH.exists():
            return {}
        try:
            with open(cls.AUTO_SALES_CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @classmethod
    def _save_auto_sales_cache(cls, cache: dict) -> None:
        try:
            cls.INFO_DIR.mkdir(parents=True, exist_ok=True)
            with open(cls.AUTO_SALES_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def _load_aeb_rows(cls) -> list[dict]:
        if cls._aeb_rows_cache is not None:
            return cls._aeb_rows_cache
        if not cls.AEB_INDEX_PATH.exists():
            cls._aeb_rows_cache = []
            return cls._aeb_rows_cache
        try:
            rows = json.loads(cls.AEB_INDEX_PATH.read_text(encoding="utf-8"))
            cls._aeb_rows_cache = rows if isinstance(rows, list) else []
        except Exception:
            cls._aeb_rows_cache = []
        return cls._aeb_rows_cache

    @staticmethod
    def _extract_year_month_from_text(text: str) -> Optional[tuple[int, int]]:
        low = (text or "").lower()
        if not low:
            return None

        # First try to bind a month to the closest explicit year. This avoids
        # taking a release year or a yearly/quarterly period as the month year.
        for month, month_re in ReportGenerator.MONTH_WORD_RE.items():
            month_to_year = re.search(
                rf"(?<![a-zа-я])(?:{month_re})(?![a-zа-я])[^0-9]{{0,90}}(?P<year>20\d{{2}})",
                low,
                flags=re.IGNORECASE,
            )
            if month_to_year:
                return int(month_to_year.group("year")), month

            year_to_month = re.search(
                rf"(?P<year>20\d{{2}})[^a-zа-я0-9]{{0,90}}(?<![a-zа-я])(?:{month_re})(?![a-zа-я])",
                low,
                flags=re.IGNORECASE,
            )
            if year_to_month:
                return int(year_to_month.group("year")), month

        y_match = re.search(r"(20\d{2})", low)
        if not y_match:
            return None
        year = int(y_match.group(1))

        for month, month_re in ReportGenerator.MONTH_WORD_RE.items():
            if re.search(
                rf"(?<![a-zа-я])(?:{month_re})(?![a-zа-я])",
                low,
                flags=re.IGNORECASE,
            ):
                return year, month
        return None

    @staticmethod
    def _extract_int_token(token: str) -> Optional[int]:
        value = re.sub(r"[^\d]", "", token or "")
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @classmethod
    def _infer_total_sales_units_from_text(cls, text: str) -> Optional[int]:
        low = (text or "").lower()
        if not low:
            return None

        # Приоритет 1: явные фразы в тексте (например "составили 140 161").
        phrase_patterns = [
            r"(?:составил[аи]?|составило|составили)\s+(\d[\d\s]{2,}\d)",
            r"(?:amounted\s+to|total(?:ed)?|reached)\s+(\d[\d\s]{2,}\d)",
        ]
        for pattern in phrase_patterns:
            for raw in re.findall(pattern, low, flags=re.IGNORECASE):
                num = cls._extract_int_token(raw)
                if num and 10_000 <= num <= 3_000_000:
                    return num

        # Приоритет 2: поиск числа рядом с единицами измерения ("шт"/"units").
        context_patterns = [
            r"(\d[\d\s]{2,}\d)\s*(?:шт|units?)",
        ]
        for pattern in context_patterns:
            for raw in re.findall(pattern, low, flags=re.IGNORECASE):
                num = cls._extract_int_token(raw)
                if num and 10_000 <= num <= 3_000_000:
                    return num

        return None

    @classmethod
    def _is_aggregate_aeb_row(cls, row: dict) -> bool:
        text = " ".join(str(row.get(k, "")) for k in ("pdf_name", "title", "period")).lower()
        aggregate_patterns = [
            r"\bq[1-4]\b",
            r"\bq[1-4]\d{2}\b",
            r"\bhy1\b",
            r"\b1hy\b",
            r"\bye\d{4}\b",
            r"\bye\s+\d{4}\b",
            r"\bannual\b",
            r"\byear\b",
            r"квартал",
            r"полугод",
            r"девять месяцев",
            r"за\s+\d+[-\s]*(?:ти\s+)?месяц",
            r"в\s+20\d{2}\s+году",
        ]
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in aggregate_patterns)

    @classmethod
    def _extract_monthly_sales_units_from_text(cls, text: str, year: int, month: int) -> Optional[int]:
        if not text:
            return None

        month_re = cls.MONTH_WORD_RE.get(month)
        if not month_re:
            return None

        normalized = cls._normalize_spaces(text)
        month_pattern = rf"(?<![a-zа-я])(?:{month_re})(?![a-zа-я])"
        direct_candidates: list[tuple[int, int, int]] = []

        for month_match in re.finditer(month_pattern, normalized, flags=re.IGNORECASE):
            before_month = normalized[max(0, month_match.start() - 14):month_match.start()]
            if re.search(r"[-–—]\s*$", before_month):
                continue

            segment = normalized[month_match.start():month_match.start() + 320]
            low_segment = segment.lower()
            for match in re.finditer(
                r"(?:составил[аио]?|составило|были\s+продан[ыо]?|продан[ыо]?|"
                r"достиг(?:ли|ло)?)\s+(\d[\d\s,.]{2,20}\d)",
                segment,
                flags=re.IGNORECASE,
            ):
                nearby = segment[max(0, match.start(1) - 12):match.end(1) + 12].lower()
                if re.search(r"\d{4}\s*/\s*\d{4}", nearby):
                    continue
                value = cls._extract_int_token(match.group(1))
                if value is None or value == year or not (10_000 <= value <= 3_000_000):
                    continue

                prefix = low_segment[:match.start()]
                score = 100 - len(prefix)
                if str(year) in prefix:
                    score += 20
                if "общие продажи" in low_segment:
                    score += 20
                if "комитета автопроизводителей" in low_segment or "аеб" in low_segment:
                    score += 8
                if "ппк" not in low_segment and "ppk" not in low_segment:
                    score += 5
                if re.search(
                    r"квартал|полугод|девять месяцев|за\s+\d+[-\s]*(?:ти\s+)?месяц|"
                    r"январ\w*\s*[-–—]",
                    prefix,
                ):
                    score -= 160

                direct_candidates.append((score, -month_match.start(), value))

        if direct_candidates:
            direct_candidates.sort(reverse=True)
            return direct_candidates[0][2]

        sentences = re.split(r"(?<=[.!?])\s+", normalized)
        candidates: list[tuple[int, int, int, int]] = []

        sentence_chunks: list[tuple[int, str]] = []
        for idx, sentence in enumerate(sentences):
            sentence_chunks.append((idx, sentence))
            if idx + 1 < len(sentences):
                sentence_chunks.append((idx, f"{sentence} {sentences[idx + 1]}"))

        for sentence_idx, sentence in sentence_chunks:
            low = sentence.lower()
            if not re.search(month_pattern, low, flags=re.IGNORECASE):
                continue

            if not any(token in low for token in ("продаж", "рын", "состав", "продан", "достиг")):
                continue

            month_match = re.search(
                month_pattern,
                low,
                flags=re.IGNORECASE,
            )
            month_pos = month_match.start() if month_match else 0
            for match in re.finditer(r"(?<!\d)(\d[\d\s,.]{2,20}\d)(?!\d)", sentence):
                nearby = sentence[max(0, match.start() - 12):match.end() + 12].lower()
                if re.search(r"\d{4}\s*/\s*\d{4}", nearby):
                    continue
                if "тел" in nearby or nearby.strip().startswith("+"):
                    continue

                value = cls._extract_int_token(match.group(1))
                if value is None or value == year or not (10_000 <= value <= 3_000_000):
                    continue

                prefix = sentence[max(0, match.start() - 90):match.start()].lower()
                score = 100
                if str(year) in low:
                    score += 8
                if "ппк" not in low and "ppk" not in low:
                    score += 5
                if match.start() > month_pos:
                    score += 12
                if re.search(r"составил[аио]?|составило|продан[ыо]?|достиг", low):
                    score += 6
                if re.search(r"составил[аио]?|составило|продан[ыо]?|достиг", prefix):
                    score += 28
                if re.search(month_pattern, prefix, flags=re.IGNORECASE):
                    score += 22
                if re.search(
                    r"квартал|полугод|девять месяцев|за\s+\d+[-\s]*(?:ти\s+)?месяц|"
                    r"январ\w*\s*[-–—]",
                    prefix,
                ):
                    score -= 85
                if re.search(r"или\s+на|больше|меньше|выше|ниже", prefix[-35:]):
                    score -= 22
                if "общие продажи" in low:
                    score += 35
                if "комитета автопроизводителей" in low or "аеб" in low:
                    score += 10

                candidates.append((score, -sentence_idx, -match.start(), value))

        if not candidates:
            return None

        candidates.sort(reverse=True)
        return candidates[0][3]

    @classmethod
    def _get_auto_sales_from_local_aeb(cls, year: int, month: int) -> Optional[AutoSalesStats]:
        rows = cls._load_aeb_rows()
        if not rows:
            return None

        primary: list[dict] = []
        aggregate: list[dict] = []
        for row in rows:
            name_text = " ".join(
                str(row.get(k, ""))
                for k in ("pdf_name", "pdf_url", "local_pdf_path")
            )
            text = " ".join(
                str(row.get(k, ""))
                for k in ("pdf_name", "title", "period", "pdf_url", "local_pdf_path")
            )
            ym = cls._extract_year_month_from_text(name_text) or cls._extract_year_month_from_text(text)
            if ym != (year, month):
                continue

            if cls._is_aggregate_aeb_row(row):
                aggregate.append(row)
            else:
                primary.append(row)

        candidates = primary if primary else aggregate
        if not candidates:
            return None

        def score(r: dict) -> tuple:
            monthly_total = cls._extract_monthly_sales_units_from_text(
                r.get("first_page_text", ""), year, month
            )
            has_total = 1 if r.get("total_sales_units") is not None else 0
            has_monthly_total = 1 if monthly_total is not None else 0
            release = r.get("release_date") or ""
            return (has_monthly_total, has_total, release)

        best = sorted(candidates, key=score, reverse=True)[0]
        is_aggregate = best in aggregate
        monthly_total = cls._extract_monthly_sales_units_from_text(
            best.get("first_page_text", ""), year, month
        )
        total_raw = best.get("total_sales_units")
        indexed_total = int(total_raw) if total_raw is not None else None

        if not is_aggregate:
            total_int = indexed_total if indexed_total is not None else monthly_total
        elif indexed_total is not None and indexed_total <= 220_000:
            total_int = indexed_total
        elif monthly_total is not None:
            total_int = monthly_total
        else:
            total_int = None

        if total_int is None and not is_aggregate:
            total_int = cls._infer_total_sales_units_from_text(best.get("first_page_text", ""))
        local_pdf = best.get("local_pdf_path") or ""
        source_url = best.get("pdf_url") or local_pdf

        if total_int is None:
            return AutoSalesStats(
                source_url=source_url,
                status="error",
                details=(
                    "В локальном AEB-индексе найден PDF за период, "
                    "но месячное значение продаж не удалось выделить из текста."
                ),
            )

        details = (
            "Локальный индекс AEB: "
            f"({best.get('pdf_name', 'без имени')}, релиз {best.get('release_date', 'n/a')})"
        )
        if is_aggregate and monthly_total is not None and total_int == monthly_total:
            details += ". Релиз содержит также агрегированный период; использовано месячное значение из текста."
        elif is_aggregate:
            details += ". Релиз содержит также агрегированный период; использовано месячное значение из индекса."
        else:
            details += "."

        return AutoSalesStats(
            source_url=source_url,
            status="ok",
            total_sales=total_int,
            top_brands=None,
            details=details,
        )

    @classmethod
    def _get_pdf_path(cls, year: int, month: int) -> Optional[Path]:
        # Используем список найденных файлов, а не одно имя:
        # реальные файлы могут содержать суффиксы вроде "_2" или "(3)".
        candidates = [path for y, m, path in cls._scan_periods() if y == year and m == month]
        if not candidates:
            return None
        # Если есть «каноничное» имя без суффиксов, выбираем его.
        exact = f"osn-{month:02d}-{year}.pdf"
        for path in candidates:
            if path.name.lower() == exact:
                return path
        return sorted(candidates, key=lambda p: len(p.name))[0]

    @classmethod
    def _strip_html(cls, html_text: str) -> str:
        cleaned = re.sub(r"(?is)<script.*?>.*?</script>", " ", html_text)
        cleaned = re.sub(r"(?is)<style.*?>.*?</style>", " ", cleaned)
        cleaned = re.sub(r"(?is)<[^>]+>", " ", cleaned)
        cleaned = unescape(cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def _parse_table_rows(cls, html_text: str) -> list[list[str]]:
        rows: list[list[str]] = []
        for tr in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", html_text):
            cells = re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr)
            parsed_cells: list[str] = []
            for cell in cells:
                text = cls._strip_html(cell)
                if text:
                    parsed_cells.append(text)
            if parsed_cells:
                rows.append(parsed_cells)
        return rows

    @staticmethod
    def _extract_first_int(text: str) -> Optional[int]:
        # Значения типа "22 289", "22,289", "22289".
        m = re.search(r"(?<!\d)(\d[\d\s,]{1,20}\d|\d)(?!\d)", text)
        if not m:
            return None
        raw = m.group(1).replace(" ", "").replace(",", "")
        try:
            return int(raw)
        except ValueError:
            return None

    @classmethod
    def _extract_auto_sales_from_html(cls, html_text: str, source_url: str) -> AutoSalesStats:
        lowered = html_text.lower()
        if "request has been denied" in lowered or "доступ запрещ" in lowered:
            return AutoSalesStats(
                source_url=source_url,
                status="error",
                details="Сайт вернул отказ в доступе (anti-bot / 403).",
            )

        rows = cls._parse_table_rows(html_text)
        if not rows:
            return AutoSalesStats(
                source_url=source_url,
                status="error",
                details="На странице не найдены табличные данные по продажам.",
            )

        total_sales: Optional[int] = None
        ranked: list[tuple[str, int]] = []

        for row in rows:
            name = row[0].strip()
            if not name:
                continue

            numbers = [cls._extract_first_int(cell) for cell in row[1:]]
            numbers = [n for n in numbers if n is not None]
            if not numbers:
                # Иногда число продаж находится в той же ячейке, что и бренд.
                fallback_n = cls._extract_first_int(" ".join(row))
                if fallback_n is None:
                    continue
                numbers = [fallback_n]

            value = numbers[0]
            low_name = name.lower()
            if any(token in low_name for token in ("всего", "итого", "total", "all brands")):
                total_sales = value
                continue
            if len(name) <= 2:
                continue
            ranked.append((name, value))

        ranked.sort(key=lambda x: x[1], reverse=True)
        top = ranked[:5]

        if not top and total_sales is None:
            return AutoSalesStats(
                source_url=source_url,
                status="error",
                details="Не удалось распознать продажи по брендам/итогам на странице.",
            )

        return AutoSalesStats(
            source_url=source_url,
            status="ok",
            total_sales=total_sales,
            top_brands=top if top else None,
            details="Данные получены с auto.vercity.ru",
        )

    @classmethod
    def _get_auto_sales_stats(cls, year: int, month: int) -> AutoSalesStats:
        local_stats = cls._get_auto_sales_from_local_aeb(year, month)
        if local_stats is not None:
            return local_stats

        if not cls.ENABLE_ONLINE_AUTO_SALES_FALLBACK:
            return AutoSalesStats(
                source_url=str(cls.AEB_INDEX_PATH),
                status="error",
                details=(
                    "В локальном индексе AEB нет данных за выбранный период "
                    f"({month:02d}.{year})."
                ),
            )

        url = cls.AUTO_SALES_URL_TEMPLATE.format(year=year, month=month)
        cache_key = f"{year:04d}-{month:02d}"
        cache = cls._load_auto_sales_cache()

        try:
            resp = requests.get(url, headers=cls.AUTO_SALES_HEADERS, timeout=20)
            html_text = resp.text if resp.text else ""
            parsed = cls._extract_auto_sales_from_html(html_text, url)

            if parsed.status == "ok":
                cache[cache_key] = {
                    "fetched_at": datetime.now().isoformat(timespec="seconds"),
                    "source_url": parsed.source_url,
                    "status": parsed.status,
                    "total_sales": parsed.total_sales,
                    "top_brands": parsed.top_brands,
                    "details": parsed.details,
                }
                cls._save_auto_sales_cache(cache)
                return parsed

            # Если онлайн-запрос не удался или заблокирован, пробуем взять кэш.
            cached = cache.get(cache_key)
            if cached:
                return AutoSalesStats(
                    source_url=cached.get("source_url", url),
                    status="cached",
                    total_sales=cached.get("total_sales"),
                    top_brands=cached.get("top_brands"),
                    details=(
                        "Онлайн-доступ к auto.vercity.ru недоступен, использованы кэшированные данные "
                        f"({cached.get('fetched_at', 'дата неизвестна')})."
                    ),
                )
            return parsed
        except Exception as exc:
            cached = cache.get(cache_key)
            if cached:
                return AutoSalesStats(
                    source_url=cached.get("source_url", url),
                    status="cached",
                    total_sales=cached.get("total_sales"),
                    top_brands=cached.get("top_brands"),
                    details=(
                        "Ошибка онлайн-запроса, использованы кэшированные данные "
                        f"({cached.get('fetched_at', 'дата неизвестна')})."
                    ),
                )
            error_text = str(exc).lower()
            if "proxy" in error_text:
                reason = "Сетевой доступ ограничен (proxy)."
            elif "403" in error_text or "denied" in error_text:
                reason = "Сайт отклонил запрос (403/anti-bot)."
            else:
                reason = "Ошибка сетевого запроса к источнику."
            return AutoSalesStats(
                source_url=url,
                status="error",
                details=reason,
            )

    @classmethod
    def get_available_years(cls) -> list[int]:
        return sorted({year for year, _, _ in cls._scan_periods()})

    @classmethod
    def get_available_months(cls, year: int) -> list[int]:
        return [month for y, month, _ in cls._scan_periods() if y == year]

    @classmethod
    def _read_pdf_text(cls, pdf_path: Path) -> str:
        cached = cls._text_cache.get(pdf_path)
        if cached is not None:
            return cached

        reader = PdfReader(str(pdf_path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        cls._text_cache[pdf_path] = text
        return text

    @staticmethod
    def _normalize_spaces(text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        return text

    @classmethod
    def _extract_period_label(cls, text: str, fallback_month: int, fallback_year: int) -> str:
        first_chunk = cls._normalize_spaces(" ".join(text.splitlines()[:40])).lower()
        month_word = (
            r"январ(?:ь|я|е)?|феврал(?:ь|я|е)?|март(?:а|е)?|апрел(?:ь|я|е)?|"
            r"ма(?:й|я|е)|июн(?:ь|я|е)?|июл(?:ь|я|е)?|август(?:а|е)?|"
            r"сентябр(?:ь|я|е)?|октябр(?:ь|я|е)?|ноябр(?:ь|я|е)?|декабр(?:ь|я|е)?"
        )
        range_match = re.search(
            rf"(?P<start>{month_word})\s*[-–—]\s*(?P<end>{month_word})\s+"
            r"(?P<year>\d{4})\s+год[а]?",
            first_chunk,
            flags=re.IGNORECASE,
        )
        if range_match:
            return (
                f"{range_match.group('start')}-{range_match.group('end')} "
                f"{range_match.group('year')} года"
            )

        year_only_match = re.search(r"\b(?P<year>20\d{2})\s+год\b", first_chunk)
        if year_only_match and fallback_month == 12:
            return f"{year_only_match.group('year')} год"

        m = re.search(
            rf"({month_word})\s+(\d{{4}})\s+года",
            first_chunk,
            flags=re.IGNORECASE,
        )
        if m:
            return f"{m.group(1)} {m.group(2)} года"

        return f"{cls.get_month_name_genitive(fallback_month)} {fallback_year} года"

    @classmethod
    def _extract_metrics(cls, text: str, month: int, year: int) -> PdfMetrics:
        metrics = PdfMetrics(
            period_label=cls._extract_period_label(text, month, year)
        )

        lines = [cls._normalize_spaces(line).strip() for line in text.splitlines()]
        num_re = re.compile(r"\d[\d ]*,\d+|\d+")

        for idx, line in enumerate(lines):
            low = line.lower()

            if "оборот розничной торговли, млрд рублей" in low and not metrics.retail_turnover_bln:
                nums = num_re.findall(line)
                if len(nums) >= 2:
                    metrics.retail_turnover_bln = nums[0]
                    metrics.retail_trade_yoy_pct = nums[1]
                continue

            if "индекс потребительских цен" in low and not metrics.cpi_yoy_pct:
                nums = num_re.findall(line)
                if len(nums) >= 2:
                    metrics.cpi_yoy_pct = nums[0]
                    metrics.cpi_month_pct = nums[1]
                continue

            if "индекс промышленного производства" in low and not metrics.industrial_yoy_pct:
                nums = num_re.findall(line)
                if len(nums) >= 1:
                    metrics.industrial_yoy_pct = nums[0]
                continue

            if "общая численность безработных" in low and not metrics.unemployment_mln:
                merged = line
                if idx + 1 < len(lines):
                    merged = f"{line} {lines[idx + 1]}"
                nums = num_re.findall(merged)
                nums_decimal = [n for n in nums if "," in n]
                if len(nums_decimal) >= 2:
                    metrics.unemployment_mln = nums_decimal[0]
                    metrics.unemployment_yoy_pct = nums_decimal[1]
                continue

        return metrics

    @classmethod
    def _find_snippet(cls, text: str, keyword: str, context: int = 380) -> Optional[str]:
        lower_text = text.lower()
        idx = lower_text.find(keyword.lower())
        if idx == -1:
            return None

        start = max(0, idx - context)
        end = min(len(text), idx + context)
        snippet = cls._normalize_spaces(text[start:end]).strip()
        return snippet if len(snippet) > 30 else None

    @classmethod
    def _snippet_score(cls, snippet: str) -> float:
        if not snippet:
            return 0.0
        letters = sum(ch.isalpha() for ch in snippet)
        digits = sum(ch.isdigit() for ch in snippet)
        total = max(1, len(snippet))
        # Prefer text-heavy snippets over table-heavy fragments.
        return (letters / total) - (digits / total) * 0.5

    @classmethod
    def _find_best_snippet(cls, text: str, keywords: list[str], context: int = 340) -> Optional[str]:
        lower = text.lower()
        best: Optional[str] = None
        best_score = -1.0

        for keyword in keywords:
            start_pos = 0
            key = keyword.lower()
            while True:
                idx = lower.find(key, start_pos)
                if idx == -1:
                    break

                start = max(0, idx - context)
                end = min(len(text), idx + context)
                candidate = cls._normalize_spaces(text[start:end]).strip()
                score = cls._snippet_score(candidate)
                if score > best_score and len(candidate) > 30:
                    best = candidate
                    best_score = score
                start_pos = idx + len(key)

        return best

    @classmethod
    def _clean_excerpt(cls, text: Optional[str], max_len: int = 520) -> str:
        if not text:
            return "Раздел не найден автоматически."

        cleaned = cls._normalize_spaces(text)
        cleaned = re.sub(r"\s*-\s*\n\s*", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if len(cleaned) <= max_len:
            return cleaned
        return f"{cleaned[:max_len].rstrip()}..."

    @staticmethod
    def _fmt_metric_line(label: str, value: Optional[str]) -> str:
        rendered = value if value else "н/д"
        return f"{label:.<44} {rendered}"

    @classmethod
    def _build_key_facts(cls, metrics: PdfMetrics, month: int, year: int) -> list[str]:
        facts: list[str] = [
            cls._fmt_metric_line(
                "Период отчета",
                metrics.period_label,
            ),
            cls._fmt_metric_line(
                "Оборот розничной торговли",
                f"{metrics.retail_turnover_bln} млрд руб." if metrics.retail_turnover_bln else None,
            ),
            cls._fmt_metric_line(
                "Розница к прошлому году",
                f"{metrics.retail_trade_yoy_pct}%" if metrics.retail_trade_yoy_pct else None,
            ),
            cls._fmt_metric_line(
                "ИПЦ к прошлому году",
                f"{metrics.cpi_yoy_pct}%" if metrics.cpi_yoy_pct else None,
            ),
            cls._fmt_metric_line(
                "ИПЦ к предыдущему месяцу",
                f"{metrics.cpi_month_pct}%" if metrics.cpi_month_pct else None,
            ),
            cls._fmt_metric_line(
                "Безработные (15+)",
                f"{metrics.unemployment_mln} млн чел." if metrics.unemployment_mln else None,
            ),
            cls._fmt_metric_line(
                "Безработица к прошлому году",
                f"{metrics.unemployment_yoy_pct}%" if metrics.unemployment_yoy_pct else None,
            ),
            cls._fmt_metric_line(
                "Промпроизводство к прошлому году",
                f"{metrics.industrial_yoy_pct}%" if metrics.industrial_yoy_pct else None,
            ),
        ]

        summary_parts: list[str] = []
        if metrics.retail_trade_yoy_pct:
            summary_parts.append(f"розница {metrics.retail_trade_yoy_pct}% г/г")
        if metrics.cpi_yoy_pct:
            summary_parts.append(f"ИПЦ {metrics.cpi_yoy_pct}% г/г")
        if metrics.industrial_yoy_pct:
            summary_parts.append(f"промпроизводство {metrics.industrial_yoy_pct}% г/г")
        if metrics.unemployment_mln:
            summary_parts.append(f"безработные {metrics.unemployment_mln} млн")

        if summary_parts:
            facts.append("")
            facts.append(
                f"Итог за {metrics.period_label}: " + "; ".join(summary_parts) + "."
            )

        return facts

    @staticmethod
    def _format_auto_sales_block(stats: AutoSalesStats) -> str:
        lines: list[str] = []

        if stats.status in ("ok", "cached"):
            total = f"{stats.total_sales:,}".replace(",", " ") if stats.total_sales is not None else "н/д"
            lines.append(f"Общий объем продаж: {total} авто.")

            if stats.top_brands:
                lines.append("Топ-5 брендов по продажам:")
                for idx, (brand, sales) in enumerate(stats.top_brands, start=1):
                    sales_text = f"{sales:,}".replace(",", " ")
                    lines.append(f"{idx}. {brand} — {sales_text}")
            else:
                lines.append("Детализация по брендам для этого источника не выделена.")

            lines.append(f"Источник: {stats.source_url}")
            if stats.details:
                lines.append(f"Статус: {stats.details}")
            return "\n".join(lines)

        lines.append("Данные о продажах авто недоступны для текущего периода.")
        if stats.details:
            lines.append(f"Причина: {stats.details}")
        lines.append(f"Ссылка: {stats.source_url}")
        return "\n".join(lines)

    @classmethod
    def generate_report(cls, year: int, month: int) -> str:
        pdf_path = cls._get_pdf_path(year, month)
        if not pdf_path:
            return f"Файл отчета не найден: info/osn-{month:02d}-{year}.pdf"

        try:
            text = cls._read_pdf_text(pdf_path)
        except Exception as exc:
            return f"Ошибка чтения PDF {pdf_path.name}: {exc}"

        metrics = cls._extract_metrics(text, month, year)
        auto_sales = cls._get_auto_sales_stats(year, month)

        summary_prod = cls._find_best_snippet(
            text,
            ["промышленного производства", "индекс промышленного производства", "производство товаров и услуг"],
        )
        summary_retail = cls._find_best_snippet(
            text,
            ["розничная торговля", "оборот розничной торговли", "рынки товаров и услуг"],
        )
        summary_prices = cls._find_best_snippet(
            text,
            ["индекс потребительских цен", "потребительские цены", "цены производителей"],
        )
        summary_labor = cls._find_best_snippet(
            text,
            ["занятость и безработица", "общая численность безработных", "уровень безработицы"],
        )
        separator = "=" * 78
        sub_separator = "-" * 78

        report = f"""СОЦИАЛЬНО-ЭКОНОМИЧЕСКИЙ ОТЧЕТ
КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ
{sub_separator}
{chr(10).join(cls._build_key_facts(metrics, month, year))}

КРАТКИЕ ВЫДЕРЖКИ ИЗ ДОКУМЕНТА
{sub_separator}
[1] ПРОИЗВОДСТВО
{cls._clean_excerpt(summary_prod)}

[2] РОЗНИЧНАЯ ТОРГОВЛЯ
{cls._clean_excerpt(summary_retail)}

[3] ЦЕНЫ
{cls._clean_excerpt(summary_prices)}

[4] ЗАНЯТОСТЬ И БЕЗРАБОТИЦА
{cls._clean_excerpt(summary_labor)}

СТАТИСТИКА ПРОДАЖ АВТОМОБИЛЕЙ (AEB PDF)
{sub_separator}
{cls._format_auto_sales_block(auto_sales)}
"""
        return report


class ReportApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Генератор социально-экономических отчетов РФ")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        self._setup_ui()

    def _setup_ui(self):
        """Настройка интерфейса приложения."""
        # Строка 0 / колонка 0: корневой контейнер для всех виджетов.
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # Строка 0: заголовок отчета.
        title_label = ttk.Label(
            main_frame,
            text="Социально-экономическое положение Российской Федерации",
            font=("Arial", 14, "bold"),
        )
        title_label.grid(row=0, column=0, pady=(0, 10))

        # Строка 1: панель выбора периода (месяц/год).
        date_frame = ttk.LabelFrame(main_frame, text="Выбор периода", padding="10")
        date_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        date_frame.columnconfigure(1, weight=1)
        date_frame.columnconfigure(3, weight=1)

        self.available_years = ReportGenerator.get_available_years()

        if not self.available_years:
            messagebox.showerror(
                "Ошибка",
                "Не найдено PDF-файлов в папке info.\n"
                "Ожидаемый шаблон имени: osn-MM-YYYY.pdf",
            )
            return

        # Строка 1, колонки 0..3:
        # Колонка 0 - подпись "Месяц", колонка 1 - список месяцев,
        # колонка 2 - подпись "Год",   колонка 3 - список годов.
        ttk.Label(date_frame, text="Месяц:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.month_var = tk.StringVar()
        self.month_label_to_num: dict[str, int] = {}
        self.month_combo = ttk.Combobox(
            date_frame,
            textvariable=self.month_var,
            state="readonly",
            width=20,
        )
        self.month_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 20))

        ttk.Label(date_frame, text="Год:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.year_var = tk.StringVar()
        self.year_combo = ttk.Combobox(
            date_frame,
            textvariable=self.year_var,
            values=[str(y) for y in self.available_years],
            state="readonly",
            width=15,
        )
        self.year_combo.grid(row=0, column=3, sticky=(tk.W, tk.E))
        self.year_combo.bind("<<ComboboxSelected>>", self._on_year_selected)

        # По умолчанию выбираем последний год, где доступно больше одного месяца.
        default_year = self.available_years[-1]
        for y in reversed(self.available_years):
            if len(ReportGenerator.get_available_months(y)) > 1:
                default_year = y
                break
        self.year_var.set(str(default_year))
        self._update_months(default_year)

        # Строка 2: кнопки действий.
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        generate_btn = ttk.Button(
            buttons_frame,
            text="Сгенерировать отчет",
            command=self.generate_report,
        )
        generate_btn.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        export_btn = ttk.Button(
            buttons_frame,
            text="Экспорт в файл",
            command=self.export_report,
        )
        export_btn.grid(row=0, column=1, sticky=tk.W)

        # Строка 3: прокручиваемая область вывода отчета.
        report_frame = ttk.LabelFrame(main_frame, text="Отчет", padding="10")
        report_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        report_frame.columnconfigure(0, weight=1)
        report_frame.rowconfigure(0, weight=1)

        self.report_text = scrolledtext.ScrolledText(
            report_frame,
            wrap=tk.WORD,
            width=100,
            height=30,
            font=("Segoe UI", 10),
            padx=10,
            pady=10,
            spacing1=2,
            spacing3=2,
        )
        self.report_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Строка 4: строка статуса.
        self.status_var = tk.StringVar(value="Готово")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
        )
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

    def _update_months(self, year: int):
        available_months = ReportGenerator.get_available_months(year)
        if available_months:
            # Формат значения в списке: "MM - название месяца" для наглядности.
            labels: list[str] = []
            self.month_label_to_num.clear()
            for m in available_months:
                label = f"{m:02d} - {ReportGenerator.get_month_name_nominative(m)}"
                labels.append(label)
                self.month_label_to_num[label] = m

            self.month_combo["values"] = labels
            self.month_var.set(labels[-1])
        else:
            self.month_combo["values"] = []
            self.month_var.set("")

    def _on_year_selected(self, event):
        year = int(self.year_var.get())
        self._update_months(year)

    def generate_report(self):
        try:
            year = int(self.year_var.get())
            month_label = self.month_var.get().strip()
            month = self.month_label_to_num.get(month_label)
            if month is None:
                # Обратная совместимость: старый формат значения "MM".
                month = int(month_label.split(" ")[0])

            report = ReportGenerator.generate_report(year, month)

            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, report)

            month_name = ReportGenerator.get_month_name_genitive(month)
            self.status_var.set(f"Отчет сгенерирован: {month_name} {year} года")

        except ValueError as exc:
            messagebox.showerror("Ошибка", f"Ошибка ввода: {exc}")
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {exc}")

    def export_report(self):
        report_content = self.report_text.get(1.0, tk.END)
        if not report_content.strip():
            messagebox.showwarning("Внимание", "Сначала сгенерируйте отчет")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
            initialfile=f"report_{self.year_var.get()}_{self.month_var.get()}.txt",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(report_content)
                self.status_var.set(f"Отчет экспортирован: {file_path}")
                messagebox.showinfo("Успех", f"Отчет успешно сохранен:\n{file_path}")
            except Exception as exc:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении: {exc}")

    def run(self):
        self.root.mainloop()


def main():
    app = ReportApp()
    app.run()


if __name__ == "__main__":
    main()
