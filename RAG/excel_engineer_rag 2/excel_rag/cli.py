from __future__ import annotations

import argparse
from pathlib import Path

from .extractor import extract_sheet_documents
from .gemini_answer import answer_with_gemini
from .retriever import BM25Retriever, format_context, load_jsonl


def build_index(args: argparse.Namespace) -> None:
    docs = extract_sheet_documents(
        workbook_path=args.workbook,
        sheet_name=args.sheet,
        output_jsonl=args.output,
        only_formulas=args.only_formulas,
        include_section_context=not args.no_section_context,
    )
    formula_count = sum(1 for d in docs if d.formula)
    print(f"Indexed {len(docs)} cells from sheet '{args.sheet}'.")
    print(f"Formula cells: {formula_count}")
    print(f"Saved index: {args.output}")


def query_index(args: argparse.Namespace) -> None:
    docs = load_jsonl(args.index)
    retriever = BM25Retriever(docs)
    results = retriever.search(args.question, top_k=args.top_k)
    context = format_context(results, max_chars=args.max_chars)
    answer = answer_with_gemini(args.question, context, model=args.model) if args.gemini else context
    print(answer)


def main() -> None:
    parser = argparse.ArgumentParser(description="Formula-aware RAG for engineering Excel workbooks")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Extract workbook sheet into JSONL index")
    p_build.add_argument("--workbook", required=True, help="Path to .xlsx workbook")
    p_build.add_argument("--sheet", default="Vibration", help="Calculation sheet name")
    p_build.add_argument("--output", default="index/vibration_cells.jsonl", help="Output JSONL index path")
    p_build.add_argument("--only-formulas", action="store_true", help="Index only formula cells")
    p_build.add_argument("--no-section-context", action="store_true", help="Disable logical section context extraction")
    p_build.set_defaults(func=build_index)

    p_query = sub.add_parser("query", help="Search index and optionally ask Gemini")
    p_query.add_argument("--index", default="index/vibration_cells.jsonl", help="JSONL index path")
    p_query.add_argument("--question", required=True, help="User question")
    p_query.add_argument("--top-k", type=int, default=8)
    p_query.add_argument("--max-chars", type=int, default=12000)
    p_query.add_argument("--gemini", action="store_true", help="Use Gemini API for final answer")
    p_query.add_argument("--model", default="gemini-3-flash-preview")
    p_query.set_defaults(func=query_index)

    args = parser.parse_args()
    Path("index").mkdir(exist_ok=True)
    args.func(args)


if __name__ == "__main__":
    main()
