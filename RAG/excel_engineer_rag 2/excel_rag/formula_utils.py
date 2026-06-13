from __future__ import annotations

import re
from dataclasses import dataclass

CELL_REF_RE = re.compile(
    r"(?:(?:'[^']+'|[A-Za-z0-9_ ]+)!)?\$?[A-Z]{1,3}\$?\d+"
)
RANGE_REF_RE = re.compile(
    r"(?:(?:'[^']+'|[A-Za-z0-9_ ]+)!)?\$?[A-Z]{1,3}\$?\d+\s*:\s*\$?[A-Z]{1,3}\$?\d+"
)


def normalize_formula(formula: str | None) -> str:
    if not formula:
        return ""
    return formula.strip()


def extract_references(formula: str | None) -> list[str]:
    """Extract cell/range references from an Excel formula.

    This is intentionally conservative. It is good enough for retrieval,
    but not a full Excel parser.
    """
    if not formula:
        return []

    refs: list[str] = []
    for match in RANGE_REF_RE.findall(formula):
        refs.append(match.replace("$", "").replace(" ", ""))

    for match in CELL_REF_RE.findall(formula):
        clean = match.replace("$", "")
        # Avoid adding cells already covered inside an explicit range string.
        if not any(clean in r for r in refs):
            refs.append(clean)

    seen = set()
    unique: list[str] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            unique.append(ref)
    return unique


@dataclass
class FormulaRisk:
    level: str
    reasons: list[str]


def detect_formula_risk(formula: str | None) -> FormulaRisk:
    if not formula:
        return FormulaRisk("none", [])

    f = formula.upper()
    reasons: list[str] = []
    risky_functions = [
        "INDIRECT", "OFFSET", "#REF!", "CUBEVALUE", "GETPIVOTDATA",
        "FORECAST", "VLOOKUP", "HLOOKUP", "XLOOKUP", "INDEX", "MATCH",
    ]
    for name in risky_functions:
        if name in f:
            reasons.append(name)

    if "[" in formula and "]" in formula:
        reasons.append("external_workbook_reference")

    if "#REF!" in f:
        return FormulaRisk("broken", reasons)
    if any(x in reasons for x in ["INDIRECT", "OFFSET", "external_workbook_reference"]):
        return FormulaRisk("high", reasons)
    if reasons:
        return FormulaRisk("medium", reasons)
    return FormulaRisk("low", [])


def excel_formula_to_js_hint(formula: str | None) -> str:
    """Best-effort readable JS hint, not a full compiler.

    For production, keep Gemini/LLM conversion grounded by including the
    original Excel formula and retrieved dependency context.
    """
    if not formula:
        return ""
    js = formula.strip()
    if js.startswith("="):
        js = js[1:]

    replacements = {
        "TRUE": "true",
        "FALSE": "false",
        "PI()": "Math.PI",
    }
    for k, v in replacements.items():
        js = re.sub(rf"\b{k}\b", v, js, flags=re.IGNORECASE)

    js = re.sub(r"\bMAX\(", "Math.max(", js, flags=re.IGNORECASE)
    js = re.sub(r"\bMIN\(", "Math.min(", js, flags=re.IGNORECASE)
    js = re.sub(r"\bABS\(", "Math.abs(", js, flags=re.IGNORECASE)
    js = re.sub(r"\bSQRT\(", "Math.sqrt(", js, flags=re.IGNORECASE)
    js = re.sub(r"\bPOWER\(", "Math.pow(", js, flags=re.IGNORECASE)
    js = js.replace("^", " ** ")
    return js
