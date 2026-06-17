# Excel Engineer RAG Prototype

Prototype ini dibuat untuk workbook engineering Excel dan saat ini difokuskan ke sheet perhitungan `Vibration` dari file:

```text
09032026_Vibration-Module.xlsx
```

Tujuan utama:

- membaca cell, formula, computed value, dan label sekitar cell;
- menyimpan metadata `sheet!address`, formula Excel, dependency, risk, dan nearby context;
- melakukan retrieval lokal menggunakan BM25 sederhana;
- opsional memakai Gemini API untuk menjawab dalam bahasa natural dan mengubah formula Excel menjadi JavaScript.

## Instalasi

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Build index dari sheet Vibration

```bash
python -m excel_rag.cli build \
  --workbook 09032026_Vibration-Module.xlsx \
  --sheet Vibration \
  --output index/vibration_cells.jsonl
```

Kalau ingin hanya formula cell:

```bash
python -m excel_rag.cli build \
  --workbook /path/to/09032026_Vibration-Module.xlsx \
  --sheet Vibration \
  --output index/vibration_formula_cells.jsonl \
  --only-formulas
```

## Query tanpa Gemini

Mode ini hanya menampilkan retrieved context. Cocok untuk debug retrieval.

```bash
python -m excel_rag.cli query \
  --index index/vibration_cells.jsonl \
  --question "bending stiffness formula"
```

## Query dengan Gemini

Set API key:

```bash
export GEMINI_API_KEY="isi_api_key_kamu"
```

Lalu jalankan:

```bash
python -m excel_rag.cli query \
  --index index/vibration_cells.jsonl \
  --question "Berikan rumus bending stiffness dalam Excel dan JavaScript" \
  --gemini
```

## Struktur data index

Setiap baris JSONL berisi satu `CellDocument` seperti:

```json
{
  "id": "09032026_Vibration-Module::Vibration!D340",
  "workbook": "09032026_Vibration-Module.xlsx",
  "sheet": "Vibration",
  "address": "D340",
  "label": "...",
  "value": 123,
  "formula": "=...",
  "dependencies": ["A1", "B2"],
  "risk_level": "low|medium|high|broken",
  "risk_reasons": ["INDEX", "OFFSET", "#REF!"],
  "nearby_context": {},
  "text": "teks untuk retrieval",
  "js_hint": "best effort formula JS hint"
}
```

## Catatan penting untuk engineering Excel

Prototype ini belum menjadi Excel calculation engine penuh. Ia fokus pada retrieval dan grounding formula. Untuk production, tambahkan:

1. parser formula Excel yang lebih kuat;
2. graph dependency antar sheet;
3. unit extraction yang lebih rapi;
4. validator hasil JavaScript vs computed value Excel;
5. handling named ranges, hidden sheets, merged cells, dan external workbook reference.

## Kenapa tidak langsung biarkan LLM membaca Excel?

Karena engineering Excel perlu jawaban yang traceable. Sistem ini memaksa jawaban untuk menyebut `sheet!cell`, formula asli, dependency, dan risk formula. Ini mengurangi risiko hallucination saat user meminta rumus seperti bending stiffness atau konversi formula ke JavaScript.

## Section-aware context

The builder now detects logical/visual calculation sections in the Excel sheet.
For example, formulas in the root mean square acceleration block carry this context:

- `section_title`: `Calculate the root mean square acceleration`
- `section_path`: e.g. `EN 1995-1-2:2025 > Calculate the root mean square acceleration`
- `section_range`: row range for the detected block
- `section_references`: nearby standard/equation references such as `EN 1995-1-1:2025, Equation 9.28`
- `section_calculations`: formulas, values, labels, notes, and dependencies inside the same section

Build normally:

```bash
uv run python -m excel_rag.cli build \
  --workbook ./09032026_Vibration-Module.xlsx \
  --sheet Vibration \
  --output index/vibration_cells.jsonl \
  --only-formulas
```

Disable this behavior only for debugging:

```bash
uv run python -m excel_rag.cli build \
  --workbook ./09032026_Vibration-Module.xlsx \
  --sheet Vibration \
  --output index/vibration_cells.jsonl \
  --only-formulas \
  --no-section-context
```

## Variable naming system

The build step now creates a whole-sheet cell-to-variable registry before writing JSONL.
This allows each formula cell to carry consistent engineering names:

- formula/calculated cells use `camelCase`, for example `aRms`, `kRes`, `modalMass`.
- non-formula scalar inputs/constants use `PascalCase`/capitalized names, for example `DampingFactor`, `DynamicForce`, `Span`.
- every indexed document includes:
  - `variable_name`
  - `variable_role`
  - `named_dependencies`
  - `js_formula_named`

Example:

```json
{
  "address": "D451",
  "label": "arms",
  "variable_name": "aRms",
  "variable_role": "calculated",
  "formula": "=(D447*D450*D449)/(2^0.5*2*D448*D441)",
  "named_dependencies": {
    "D447": {"name": "kRes", "role": "calculated"},
    "D450": {"name": "muRes", "role": "calculated"},
    "D449": {"name": "fDyn", "role": "calculated"}
  },
  "js_formula_named": "(kRes*muRes*fDyn)/(2 ** 0.5*2*DampingFactor*modalMass)"
}
```

The naming is heuristic and intentionally stored in JSONL so you can audit it.
If a variable name is not good enough, add a domain alias in `excel_rag/variable_naming.py` under `SYMBOL_ALIASES`.