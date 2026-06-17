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
  --workbook /path/to/09032026_Vibration-Module.xlsx \
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
