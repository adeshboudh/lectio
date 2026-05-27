"""Evaluation harness for the Christianity AI assistant.

Runs every case in dataset.json through the compiled LangGraph agent,
scores each PASS / PARTIAL / FAIL, and prints a category-grouped report.

Usage (from repo root):
    docker compose up -d
    cd backend
    uv run python ../eval/run_eval.py [--id <case-id>] [--category <cat>]

Exit code: 0 if all PASS/PARTIAL, 1 if any FAIL.
"""

import argparse
import json
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Add backend to path when run from repo root or eval dir
sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.agent.graph import get_graph
from app.core.db import close_pool
from app.logging_config import configure_logging

configure_logging(log_level="WARNING")  # suppress info noise during eval

Score = Literal["PASS", "PARTIAL", "FAIL"]

DATASET = Path(__file__).parent / "dataset.json"


@dataclass
class Result:
    case_id: str
    category: str
    description: str
    score: Score
    findings: list[str] = field(default_factory=list)
    intent: str = ""
    flagged: bool = False
    citations: int = 0
    hallucinated: list[str] = field(default_factory=list)
    error: str = ""


def run_case(graph, case: dict) -> Result:
    checks = case["checks"]
    result = Result(
        case_id=case["id"],
        category=case["category"],
        description=case["description"],
        score="PASS",
    )

    try:
        state = graph.invoke({
            "session_id": f"eval-{case['id']}",
            "user_message": case["message"],
            "denomination": case.get("denomination", "protestant"),
            "request_id": str(uuid.uuid4()),
            "messages": [],
            "latency_ms": {},
            "memory_turns": [],
        })
    except Exception as exc:
        result.score = "FAIL"
        result.error = str(exc)
        result.findings.append(f"CRASH: {exc}")
        return result

    resp_lower = state["final_response"].lower()
    result.intent = state.get("intent", "")
    result.flagged = state.get("flagged", False)
    result.citations = len(state.get("verified_citations", []))
    result.hallucinated = state.get("hallucinated_refs", [])

    failures, partials = [], []

    # --- must_be_flagged ---
    if checks.get("must_be_flagged") and not result.flagged:
        failures.append("expected flagged=True but got False")

    # --- must_not_be_flagged (explicitly) ---
    if "must_not_be_flagged" in checks and checks["must_not_be_flagged"] is False:
        pass  # fine — don't require flagged

    # --- expected_intents ---
    if "expected_intents" in checks:
        if result.intent not in checks["expected_intents"]:
            partials.append(f"intent={result.intent!r} not in {checks['expected_intents']}")

    # --- must_contain_hallucinated_ref ---
    if "must_contain_hallucinated_ref" in checks:
        ref = checks["must_contain_hallucinated_ref"]
        if ref not in result.hallucinated:
            # Check if model just never mentioned the ref (also acceptable)
            if ref.lower() in state["final_response"].lower():
                failures.append(f"hallucinated ref {ref!r} appeared in response but not caught")
            # else: ref not mentioned at all — model avoided it correctly, that's also OK

    # --- response_must_not_contain ---
    for phrase in checks.get("response_must_not_contain", []):
        if phrase.lower() in resp_lower:
            failures.append(f"response contains forbidden phrase: {phrase!r}")

    # --- response_must_contain_any ---
    required_any = checks.get("response_must_contain_any", [])
    if required_any:
        if not any(p.lower() in resp_lower for p in required_any):
            partials.append(f"response missing expected signal (one of: {required_any})")

    # --- verified_citations_min ---
    if "verified_citations_min" in checks:
        mn = checks["verified_citations_min"]
        if result.citations < mn:
            partials.append(f"citations={result.citations} < required {mn}")

    # --- verified_citations_max ---
    if "verified_citations_max" in checks:
        mx = checks["verified_citations_max"]
        if result.citations > mx:
            partials.append(f"citations={result.citations} > max allowed {mx}")

    # --- image_url_must_be_empty ---
    if checks.get("image_url_must_be_empty") and state.get("image_url"):
        failures.append("image_url is non-empty but should be blocked")

    # --- image_safety_must_be_checked ---
    if checks.get("image_safety_must_be_checked"):
        if not state.get("sanitized_image_prompt"):
            partials.append("image prompt was not rewritten (sanitized_image_prompt empty)")

    # Score
    if failures:
        result.score = "FAIL"
        result.findings.extend(failures)
    elif partials:
        result.score = "PARTIAL"
        result.findings.extend(partials)

    return result


SCORE_ICON = {"PASS": "✓", "PARTIAL": "~", "FAIL": "✗"}
SCORE_COLOR = {"PASS": "\033[32m", "PARTIAL": "\033[33m", "FAIL": "\033[31m"}
RESET = "\033[0m"


def print_report(results: list[Result]) -> bool:
    by_cat: dict[str, list[Result]] = {}
    for r in results:
        by_cat.setdefault(r.category, []).append(r)

    totals = {"PASS": 0, "PARTIAL": 0, "FAIL": 0}
    any_fail = False

    for cat, cat_results in sorted(by_cat.items()):
        print(f"\n{'─' * 70}")
        print(f"  {cat.upper()}")
        print(f"{'─' * 70}")
        for r in cat_results:
            color = SCORE_COLOR[r.score]
            icon = SCORE_ICON[r.score]
            totals[r.score] += 1
            if r.score == "FAIL":
                any_fail = True
            print(
                f"  {color}{icon} {r.score:<7}{RESET}  [{r.case_id}]  {r.description}"
            )
            print(
                f"           intent={r.intent!r}  flagged={r.flagged}"
                f"  citations={r.citations}  hall={len(r.hallucinated)}"
            )
            for finding in r.findings:
                print(f"           ↳ {finding}")
            if r.error:
                print(f"           ↳ ERROR: {r.error}")

    print(f"\n{'═' * 70}")
    print(
        f"  RESULTS:  "
        f"{SCORE_COLOR['PASS']}PASS {totals['PASS']}{RESET}  "
        f"{SCORE_COLOR['PARTIAL']}PARTIAL {totals['PARTIAL']}{RESET}  "
        f"{SCORE_COLOR['FAIL']}FAIL {totals['FAIL']}{RESET}  "
        f"/ {sum(totals.values())} total"
    )
    print(f"{'═' * 70}\n")
    return not any_fail


def main() -> None:
    parser = argparse.ArgumentParser(description="Christianity AI eval harness")
    parser.add_argument("--id", help="Run a single case by id")
    parser.add_argument("--category", help="Run all cases in a category")
    args = parser.parse_args()

    cases = json.loads(DATASET.read_text())

    if args.id:
        cases = [c for c in cases if c["id"] == args.id]
    if args.category:
        cases = [c for c in cases if c["category"] == args.category]

    if not cases:
        print("No matching cases found.")
        sys.exit(1)

    print(f"\nRunning {len(cases)} eval case(s)...\n")
    graph = get_graph()
    results = []

    for i, case in enumerate(cases, 1):
        print(f"  [{i}/{len(cases)}] {case['id']}...", end=" ", flush=True)
        r = run_case(graph, case)
        icon = SCORE_ICON[r.score]
        print(f"{SCORE_COLOR[r.score]}{icon} {r.score}{RESET}")
        results.append(r)

    close_pool()
    ok = print_report(results)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
