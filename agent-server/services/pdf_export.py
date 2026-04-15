from __future__ import annotations

import math
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN = 36
CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2
TOP = PAGE_HEIGHT - MARGIN
BOTTOM = 42
LINE_HEIGHT = 16
BODY_FONT_SIZE = 10
SMALL_FONT_SIZE = 9
TITLE_FONT_SIZE = 22
SECTION_FONT_SIZE = 13

GREEN = (0.13, 0.48, 0.36)
ORANGE = (0.90, 0.35, 0.20)
INK = (0.10, 0.14, 0.13)
PAPER = (0.96, 0.98, 0.96)
LINE = (0.80, 0.88, 0.82)
WHITE = (1, 1, 1)


def z(value: str) -> str:
    """Keep this source ASCII-only while rendering Chinese text in the PDF."""
    return value.encode("ascii").decode("unicode_escape")


LABELS = {
    "fallback_title": z(r"\u65c5\u884c\u89c4\u5212\u62a5\u544a"),
    "subtitle": z(r"\u4e00\u4efd\u53ef\u76f4\u63a5\u51fa\u884c\u4f7f\u7528\u7684\u8def\u7ebf\u3001\u5929\u6c14\u3001\u4f4f\u5bbf\u3001\u4ea4\u901a\u4e0e\u8d39\u7528\u6e05\u5355"),
    "report_name": z(r"\u62a5\u544a\u540d\u79f0\uff1a"),
    "exported_at": z(r"\u5bfc\u51fa\u65f6\u95f4\uff1a"),
    "route_stats": z(r"\u8def\u7ebf\u56fe\uff1a"),
    "route_groups": z(r" \u7ec4\uff1b\u666f\u70b9\u6807\u8bb0\uff1a"),
    "markers": z(r" \u4e2a"),
    "use_hint": z(r"\u7528\u9014\uff1a\u51fa\u884c\u524d\u786e\u8ba4\u6bcf\u65e5\u8def\u7ebf\u3001\u4f4f\u5bbf\u4ea4\u901a\u3001\u5929\u6c14\u63d0\u9192\u548c\u8d39\u7528\u8981\u70b9\u3002"),
    "unnamed": z(r"\u672a\u547d\u540d\u5730\u70b9"),
    "route_ready": z(r"\u8def\u7ebf\u70b9\u5df2\u751f\u6210"),
    "about": z(r"\u7ea6"),
    "km": z(r" km"),
    "confirm_distance": z(r"\u8ddd\u79bb\u5f85\u73b0\u573a\u786e\u8ba4"),
    "route_points": z(r"\uff1b\u8def\u7ebf\u70b9 "),
    "points_unit": z(r" \u4e2a"),
    "no_route": z(r"\u6682\u65e0\u8def\u7ebf\u5730\u56fe\u6570\u636e\uff0c\u5efa\u8bae\u7b49\u8def\u7ebf\u56fe\u751f\u6210\u540e\u518d\u5bfc\u51fa\u3002"),
    "no_attraction": z(r"\u6682\u65e0\u660e\u786e\u666f\u70b9\u6e05\u5355\u3002"),
    "no_weather": z(r"\u6682\u65e0\u660e\u786e\u5929\u6c14\u4fe1\u606f\uff0c\u51fa\u53d1\u524d\u5efa\u8bae\u518d\u6b21\u67e5\u8be2\u5b9e\u65f6\u5929\u6c14\u3002"),
    "no_stay": z(r"\u6682\u65e0\u660e\u786e\u4f4f\u5bbf\u4fe1\u606f\uff0c\u53ef\u6309\u9884\u7b97\u548c\u8def\u7ebf\u4e2d\u5fc3\u70b9\u9009\u62e9\u9152\u5e97\u3002"),
    "no_transport": z(r"\u6682\u65e0\u660e\u786e\u4ea4\u901a\u7968\u4ef7\u4fe1\u606f\uff0c\u5efa\u8bae\u7ed3\u5408\u51fa\u53d1\u5730\u8865\u5145\u8f66\u7968\u6216\u673a\u7968\u4ef7\u683c\u3002"),
    "no_budget": z(r"\u6682\u65e0\u5b8c\u6574\u8d39\u7528\u660e\u7ec6\uff0c\u5efa\u8bae\u8865\u5145\u95e8\u7968\u3001\u4f4f\u5bbf\u3001\u9910\u996e\u548c\u4ea4\u901a\u9884\u7b97\u3002"),
    "no_food": z(r"\u6682\u65e0\u660e\u786e\u9910\u996e\u5b89\u6392\uff0c\u53ef\u6309\u6bcf\u65e5\u666f\u70b9\u9644\u8fd1\u8865\u5145\u9910\u5385\u3002"),
    "default_tips": z(r"\u5efa\u8bae\u63d0\u524d\u9884\u7ea6\u70ed\u95e8\u666f\u70b9\uff0c\u4fdd\u7559\u673a\u52a8\u65f6\u95f4\uff0c\u968f\u8eab\u643a\u5e26\u8eab\u4efd\u8bc1\u4ef6\u548c\u5145\u7535\u8bbe\u5907\u3002"),
    "empty": z(r"\u6682\u65e0\u6570\u636e"),
}

SECTION_TITLES = [
    z(r"\u884c\u7a0b\u6982\u89c8"),
    z(r"\u6bcf\u65e5\u5b89\u6392"),
    z(r"\u666f\u70b9\u63a8\u8350"),
    z(r"\u8def\u7ebf\u89c4\u5212"),
    z(r"\u5929\u6c14\u63d0\u9192"),
    z(r"\u4f4f\u5bbf\u4e0e\u9152\u5e97"),
    z(r"\u4ea4\u901a\u4e0e\u7968\u4ef7"),
    z(r"\u9910\u996e\u63a8\u8350"),
    z(r"\u8d39\u7528\u9884\u7b97"),
    z(r"\u51fa\u884c\u63d0\u9192"),
]

KEYWORDS = {
    "weather": [z(r"\u5929\u6c14"), z(r"\u6e29\u5ea6"), z(r"\u964d\u96e8"), z(r"\u4e0b\u96e8"), z(r"\u6674"), z(r"\u9634"), z(r"\u98ce"), z(r"\u7d2b\u5916\u7ebf")],
    "stays": [z(r"\u9152\u5e97"), z(r"\u4f4f\u5bbf"), z(r"\u6c11\u5bbf"), z(r"\u5165\u4f4f"), z(r"\u5ba2\u6808")],
    "transport": [z(r"\u9ad8\u94c1"), z(r"\u706b\u8f66"), z(r"\u673a\u7968"), z(r"\u8f66\u7968"), z(r"\u5730\u94c1"), z(r"\u516c\u4ea4"), z(r"\u6253\u8f66"), z(r"\u81ea\u9a7e"), z(r"\u5305\u8f66"), z(r"\u4ea4\u901a")],
    "budget": [z(r"\u9884\u7b97"), z(r"\u8d39\u7528"), z(r"\u4ef7\u683c"), z(r"\u95e8\u7968"), z(r"\u7968\u4ef7"), z(r"\u5143"), z(r"\uffe5")],
    "food": [z(r"\u65e9\u9910"), z(r"\u5348\u9910"), z(r"\u665a\u9910"), z(r"\u9910\u5385"), z(r"\u7f8e\u98df"), z(r"\u5c0f\u5403"), z(r"\u5403")],
    "tips": [z(r"\u5efa\u8bae"), z(r"\u6ce8\u610f"), z(r"\u63d0\u9192"), z(r"\u643a\u5e26"), z(r"\u9884\u7ea6"), z(r"\u907f\u5f00")],
    "attractions": [z(r"\u666f\u70b9"), z(r"\u516c\u56ed"), z(r"\u535a\u7269\u9986"), z(r"\u53e4\u9547"), z(r"\u8857"), z(r"\u6e56"), z(r"\u5c71"), z(r"\u5bfa")],
}


@dataclass
class ReportBlock:
    title: str
    lines: list[str]
    accent: tuple[float, float, float] = GREEN


def _clean_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^[#>\-\*\s]+", "", line)
    line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
    line = re.sub(r"`([^`]*)`", r"\1", line)
    line = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", line)
    return line.strip()


def _content_lines(content: str) -> list[str]:
    raw_lines = content.replace("\r", "\n").split("\n")
    return [line for line in (_clean_line(item) for item in raw_lines) if line]


def _pick_lines(lines: list[str], keywords: list[str], limit: int = 8) -> list[str]:
    picked: list[str] = []
    for line in lines:
        if any(keyword in line for keyword in keywords):
            picked.append(line)
        if len(picked) >= limit:
            break
    return picked


def _split_days(lines: list[str]) -> list[str]:
    day_lines: list[str] = []
    current: list[str] = []
    chinese_day = z(r"\u7b2c[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\\d]+[\u5929\u65e5]")
    day_pattern = re.compile(rf"(Day\s*\d+|D\d+|{chinese_day})", re.I)
    for line in lines:
        if day_pattern.search(line) and current:
            day_lines.append(" / ".join(current[:5]))
            current = [line]
        else:
            current.append(line)
    if current:
        day_lines.append(" / ".join(current[:5]))
    return day_lines[:8]


def _marker_name(marker: dict[str, Any]) -> str:
    callout = marker.get("callout") if isinstance(marker.get("callout"), dict) else {}
    return str(
        marker.get("content")
        or marker.get("name")
        or marker.get("title")
        or callout.get("content")
        or LABELS["unnamed"]
    )


def _point_value(point: dict[str, Any], key: str) -> float | None:
    try:
        value = point.get(key)
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _distance_km(points: list[dict[str, Any]]) -> float:
    def haversine(a: dict[str, Any], b: dict[str, Any]) -> float:
        lat1 = _point_value(a, "latitude")
        lon1 = _point_value(a, "longitude")
        lat2 = _point_value(b, "latitude")
        lon2 = _point_value(b, "longitude")
        if None in (lat1, lon1, lat2, lon2):
            return 0.0
        radius = 6371.0
        phi1 = math.radians(lat1 or 0)
        phi2 = math.radians(lat2 or 0)
        d_phi = math.radians((lat2 or 0) - (lat1 or 0))
        d_lam = math.radians((lon2 or 0) - (lon1 or 0))
        h = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
        return 2 * radius * math.atan2(math.sqrt(h), math.sqrt(1 - h))

    return sum(haversine(points[i - 1], points[i]) for i in range(1, len(points)))


def _route_lines(maps: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for index, item in enumerate(maps or [], start=1):
        day = str(item.get("day") or f"Day {index}")
        markers = item.get("markers") or item.get("marker") or []
        polyline = item.get("polyline") or []
        points: list[dict[str, Any]] = []
        if isinstance(polyline, list) and polyline and isinstance(polyline[0], dict):
            points = polyline[0].get("points") or []
        if not points:
            points = item.get("points") or []
        marker_names = [_marker_name(marker) for marker in markers if isinstance(marker, dict)]
        route_name = " -> ".join(marker_names[:5]) if marker_names else LABELS["route_ready"]
        distance = _distance_km(points) if isinstance(points, list) else 0
        distance_text = f"{LABELS['about']}{distance:.1f}{LABELS['km']}" if distance > 0 else LABELS["confirm_distance"]
        result.append(f"{day}: {route_name} | {distance_text}{LABELS['route_points']}{len(points)}{LABELS['points_unit']}")
    return result or [LABELS["no_route"]]


def _attraction_lines(maps: list[dict[str, Any]], content_lines: list[str]) -> list[str]:
    names: list[str] = []
    for item in maps or []:
        markers = item.get("markers") or item.get("marker") or []
        for marker in markers:
            if isinstance(marker, dict):
                name = _marker_name(marker)
                if name and name not in names:
                    names.append(name)
    if names:
        return [f"{index}. {name}" for index, name in enumerate(names[:14], start=1)]
    return _pick_lines(content_lines, KEYWORDS["attractions"], 10) or [LABELS["no_attraction"]]


def _build_report_blocks(title: str, content: str, maps: list[dict[str, Any]]) -> list[ReportBlock]:
    lines = _content_lines(content)
    route_count = len(maps or [])
    marker_count = sum(len(item.get("markers") or item.get("marker") or []) for item in maps or [])
    overview = [
        LABELS["report_name"] + (title or LABELS["fallback_title"]),
        LABELS["exported_at"] + datetime.now().strftime("%Y-%m-%d %H:%M"),
        f"{LABELS['route_stats']}{route_count}{LABELS['route_groups']}{marker_count}{LABELS['markers']}",
        LABELS["use_hint"],
    ]

    blocks_data = [
        (SECTION_TITLES[0], overview, GREEN),
        (SECTION_TITLES[1], _split_days(lines) or lines[:8], ORANGE),
        (SECTION_TITLES[2], _attraction_lines(maps, lines), GREEN),
        (SECTION_TITLES[3], _route_lines(maps), ORANGE),
        (SECTION_TITLES[4], _pick_lines(lines, KEYWORDS["weather"], 8) or [LABELS["no_weather"]], GREEN),
        (SECTION_TITLES[5], _pick_lines(lines, KEYWORDS["stays"], 8) or [LABELS["no_stay"]], ORANGE),
        (SECTION_TITLES[6], _pick_lines(lines, KEYWORDS["transport"], 8) or [LABELS["no_transport"]], GREEN),
        (SECTION_TITLES[7], _pick_lines(lines, KEYWORDS["food"], 8) or [LABELS["no_food"]], ORANGE),
        (SECTION_TITLES[8], _pick_lines(lines, KEYWORDS["budget"], 8) or [LABELS["no_budget"]], GREEN),
        (SECTION_TITLES[9], _pick_lines(lines, KEYWORDS["tips"], 8) or [LABELS["default_tips"]], ORANGE),
    ]
    return [ReportBlock(title=block_title, lines=block_lines, accent=accent) for block_title, block_lines, accent in blocks_data]


def _wrap_text(text: str, font_size: int = BODY_FONT_SIZE, width: float = CONTENT_WIDTH - 24) -> list[str]:
    char_width = max(font_size * 0.56, 5.0)
    max_chars = max(12, int(width / char_width))
    wrapped: list[str] = []
    for part in str(text).split("\n"):
        wrapped.extend(textwrap.wrap(part, width=max_chars, break_long_words=True, replace_whitespace=False) or [""])
    return wrapped


def _rgb(color: tuple[float, float, float]) -> str:
    return f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f}"


def _hex_text(text: str) -> str:
    return text.encode("utf-16-be", errors="replace").hex().upper()


class PdfCanvas:
    def __init__(self) -> None:
        self.pages: list[list[str]] = []
        self.ops: list[str] = []
        self.y = TOP
        self.add_page()

    def add_page(self) -> None:
        if self.ops:
            self.pages.append(self.ops)
        self.ops = []
        self.y = TOP
        self.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, PAPER, fill=True, stroke=False)

    def ensure(self, height: float) -> None:
        if self.y - height < BOTTOM:
            self.add_page()

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: tuple[float, float, float],
        fill: bool = True,
        stroke: bool = False,
    ) -> None:
        op = "f" if fill and not stroke else "B" if fill and stroke else "S"
        color_op = "rg" if fill else "RG"
        self.ops.append(f"q {_rgb(color)} {color_op} {x:.1f} {y:.1f} {w:.1f} {h:.1f} re {op} Q")

    def text(self, text: str, x: float, y: float, size: int = BODY_FONT_SIZE, color: tuple[float, float, float] = INK) -> None:
        self.ops.append(f"BT {_rgb(color)} rg /F1 {size} Tf 1 0 0 1 {x:.1f} {y:.1f} Tm <{_hex_text(text)}> Tj ET")

    def title(self, title: str) -> None:
        self.rect(MARGIN, self.y - 62, CONTENT_WIDTH, 62, GREEN, fill=True, stroke=False)
        self.text((title or LABELS["fallback_title"])[:32], MARGIN + 18, self.y - 30, TITLE_FONT_SIZE, WHITE)
        self.text(LABELS["subtitle"], MARGIN + 18, self.y - 52, SMALL_FONT_SIZE, WHITE)
        self.y -= 82

    def block(self, block: ReportBlock) -> None:
        rows: list[str] = []
        for line in block.lines[:16]:
            rows.extend(_wrap_text(line, BODY_FONT_SIZE, CONTENT_WIDTH - 30))
        height = 34 + max(1, len(rows)) * LINE_HEIGHT + 14
        self.ensure(height + 10)
        top = self.y
        self.rect(MARGIN, top - height, CONTENT_WIDTH, height, WHITE, fill=True, stroke=False)
        self.rect(MARGIN, top - 28, CONTENT_WIDTH, 28, block.accent, fill=True, stroke=False)
        self.text(block.title, MARGIN + 12, top - 19, SECTION_FONT_SIZE, WHITE)
        y = top - 48
        for row in rows or [LABELS["empty"]]:
            self.text(row, MARGIN + 14, y, BODY_FONT_SIZE, INK)
            y -= LINE_HEIGHT
        self.rect(MARGIN, top - height, CONTENT_WIDTH, height, LINE, fill=False, stroke=True)
        self.y = top - height - 12

    def finish(self) -> list[list[str]]:
        if self.ops:
            self.pages.append(self.ops)
            self.ops = []
        return self.pages


def _stream_bytes(ops: list[str]) -> bytes:
    return "\n".join(ops).encode("ascii")


def _build_pdf_bytes(title: str, content: str, maps: list[dict[str, Any]]) -> bytes:
    canvas = PdfCanvas()
    canvas.title(title or LABELS["fallback_title"])
    for block in _build_report_blocks(title, content, maps):
        canvas.block(block)
    page_ops = canvas.finish()

    objects: list[bytes] = []

    def add_object(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object(b"")
    font_id = add_object(
        b"<< /Type /Font /Subtype /Type0 /BaseFont /STSong-Light "
        b"/Encoding /UniGB-UCS2-H /DescendantFonts [4 0 R] >>"
    )
    add_object(
        b"<< /Type /Font /Subtype /CIDFontType0 /BaseFont /STSong-Light "
        b"/CIDSystemInfo << /Registry (Adobe) /Ordering (GB1) /Supplement 2 >> "
        b"/FontDescriptor 5 0 R >>"
    )
    add_object(
        b"<< /Type /FontDescriptor /FontName /STSong-Light /Flags 6 "
        b"/FontBBox [0 -200 1000 900] /ItalicAngle 0 /Ascent 880 "
        b"/Descent -120 /CapHeight 700 /StemV 80 >>"
    )

    page_ids: list[int] = []
    for ops in page_ops:
        stream = _stream_bytes(ops)
        content_id = add_object(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
        page_id = add_object(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode("ascii")
        )
        page_ids.append(page_id)

    objects[pages_id - 1] = (
        f"<< /Type /Pages /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] /Count {len(page_ids)} >>"
    ).encode("ascii")

    pdf = bytearray(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    return bytes(pdf)


def create_trip_pdf(
    export_dir: str | Path,
    title: str,
    content: str,
    maps: list[dict[str, Any]] | None = None,
) -> tuple[str, Path]:
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"trip-report-{uuid4().hex}.pdf"
    path = export_dir / filename
    path.write_bytes(_build_pdf_bytes(title, content[:50000], maps or []))
    return filename, path