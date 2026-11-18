"""Командная строка.

  python -m aicase.cli portfolio examples/cases --html reports/portfolio.html
  python -m aicase.cli assess examples/cases/01_support_assistant.yaml
  python -m aicase.cli assess-text "Хотим ассистента, который ..."   (нужна Ollama)
  python -m aicase.cli portfolio examples/cases --html reports/portfolio.html --summaries   (резюме от LLM)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .llm import executive_summary, extract_case
from .model import case_from_dict
from .report import console, facts, html_report
from .scoring import assess_case, rank


def load(path: Path):
    return case_from_dict(yaml.safe_load(path.read_text(encoding="utf-8")))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="aicase")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("assess")
    a.add_argument("file", type=Path)
    t = sub.add_parser("assess-text")
    t.add_argument("text")
    pf = sub.add_parser("portfolio")
    pf.add_argument("folder", type=Path)
    pf.add_argument("--html", type=Path)
    pf.add_argument("--summaries", action="store_true", help="добавить резюме от локальной LLM")
    args = p.parse_args(argv)

    if args.cmd == "assess":
        print(console(assess_case(load(args.file))))
    elif args.cmd == "assess-text":
        case = extract_case(args.text)
        print("Извлечено LLM:", case.model_dump(exclude={"assumptions"}))
        print(console(assess_case(case)))
    elif args.cmd == "portfolio":
        items = rank([load(f) for f in sorted(args.folder.glob("*.yaml"))])
        for i, item in enumerate(items, 1):
            print(f"{i}. {console(item)}\n")
        if args.html:
            summaries = {}
            if args.summaries:
                for item in items:
                    try:
                        summaries[item.case.name] = executive_summary(facts(item))
                    except Exception as e:  # модель недоступна: отчёт строится без резюме
                        print(f"резюме не получено для «{item.case.name}»: {e}", file=sys.stderr)
            args.html.parent.mkdir(parents=True, exist_ok=True)
            args.html.write_text(html_report(items, summaries=summaries), encoding="utf-8")
            print(f"Отчёт: {args.html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
