# Usage:
#   python3 analyze_results.py --input-dir results_v2 --output analysis_v2.md
#   python3 analyze_results.py --input-dir results_legacy --output analysis_legacy.md
#   python3 analyze_results.py

import argparse
import glob
import json
import os
import re
from collections import Counter, defaultdict
from statistics import mean

FILENAME_PATTERN = re.compile(r"(Control|Experimental)_R(\d+)_V(\d+)_T(\d+)_")
VOTE_OPTIONS = {"P1", "P2", "P3"}


def parse_result_file(path: str):
    name = os.path.basename(path)
    m = FILENAME_PATTERN.search(name)
    if not m:
        return None

    group, rounds, veto, trial = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = data.get("results", {})
    final_decision = result.get("final_decision", "UNKNOWN")
    intent_history = result.get("intent_history_per_round", [])
    agenda_veto_used = bool(result.get("agenda_veto_used", False))
    agenda_veto_history = result.get("agenda_veto_history", [])

    return {
        "path": path,
        "file": name,
        "group": group,
        "rounds_cfg": rounds,
        "veto_cfg": veto,
        "trial": trial,
        "final": final_decision,
        "rounds_to_end": len(intent_history),
        "history": intent_history,
        "agenda_veto_used": agenda_veto_used,
        "agenda_veto_history": agenda_veto_history,
    }


def final_bucket(final_decision: str) -> str:
    if "P1" in final_decision:
        return "P1"
    if "P2" in final_decision:
        return "P2"
    if "P3" in final_decision:
        return "P3"
    if "FAILED" in final_decision or "VETOED" in final_decision:
        return "Failed"
    return "Other"


def summarize_by_config(rows):
    by_cfg = defaultdict(list)
    for row in rows:
        by_cfg[(row["group"], row["rounds_cfg"], row["veto_cfg"])].append(row)

    output = []
    for (group, rounds_cfg, veto_cfg), arr in sorted(by_cfg.items()):
        outcomes = Counter(final_bucket(x["final"]) for x in arr)
        n = len(arr)
        avg_rounds = mean(x["rounds_to_end"] for x in arr)
        veto_triggered_count = sum(1 for x in arr if x["final"] == "VETOED")
        agenda_veto_used_count = sum(1 for x in arr if x.get("agenda_veto_used", False))
        output.append({
            "group": group,
            "rounds": rounds_cfg,
            "veto": veto_cfg,
            "n": n,
            "P1": outcomes["P1"],
            "P2": outcomes["P2"],
            "P3": outcomes["P3"],
            "Failed": outcomes["Failed"],
            "Other": outcomes["Other"],
            "avg_rounds_to_end": avg_rounds,
            "veto_triggered_count": veto_triggered_count,
            "agenda_veto_used_count": agenda_veto_used_count,
        })
    return output


def summarize_intents(rows):
    intent_counter = Counter()
    role_intent_counter = defaultdict(Counter)
    total_vote_intents = 0

    for row in rows:
        for round_item in row["history"]:
            intents = round_item.get("intents", {})
            for role, intent in intents.items():
                intent_counter[intent] += 1
                role_intent_counter[role][intent] += 1
                if intent in VOTE_OPTIONS:
                    total_vote_intents += 1

    return intent_counter, role_intent_counter, total_vote_intents


def build_markdown(rows):
    cfg_summary = summarize_by_config(rows)
    intent_counter, role_intent_counter, total_vote_intents = summarize_intents(rows)

    lines = []
    lines.append("# Simulation Summary")
    lines.append("")
    lines.append(f"- Total trials parsed: {len(rows)}")
    lines.append("")

    lines.append("## Config-Level Outcomes")
    lines.append("")
    lines.append("| Group | R | V | n | P1 | P2 | P3 | Failed | P1% | P2% | P3% | Fail% | Avg rounds to end | Legacy Veto Triggered | Legacy Veto Rate | Agenda Veto Used | Agenda Veto Rate |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for item in cfg_summary:
        n = item["n"]
        if item["veto"] == 1:
            veto_trigger_rate = f"{item['veto_triggered_count']/n:.0%}"
            agenda_veto_rate = f"{item['agenda_veto_used_count']/n:.0%}"
        else:
            veto_trigger_rate = "N/A"
            agenda_veto_rate = "N/A"
        lines.append(
            f"| {item['group']} | {item['rounds']} | {item['veto']} | {n} | {item['P1']} | {item['P2']} | {item['P3']} | {item['Failed']} | "
            f"{item['P1']/n:.0%} | {item['P2']/n:.0%} | {item['P3']/n:.0%} | {item['Failed']/n:.0%} | {item['avg_rounds_to_end']:.2f} | "
            f"{item['veto_triggered_count']} | {veto_trigger_rate} | {item['agenda_veto_used_count']} | {agenda_veto_rate} |"
        )

    lines.append("")
    lines.append("## Intent Distribution")
    lines.append("")

    vote_intents = intent_counter["P1"] + intent_counter["P2"] + intent_counter["P3"]
    if vote_intents > 0:
        lines.append(f"- Round-level vote intents: P1={intent_counter['P1']}, P2={intent_counter['P2']}, P3={intent_counter['P3']}")
        lines.append(f"- P3 share among vote intents: {intent_counter['P3']}/{vote_intents} = {intent_counter['P3']/vote_intents:.1%}")

    if total_vote_intents > 0:
        lines.append("")
        lines.append("### P3 Intent by Role")
        for role in sorted(role_intent_counter.keys()):
            role_votes = sum(role_intent_counter[role][k] for k in VOTE_OPTIONS)
            p3_votes = role_intent_counter[role]["P3"]
            ratio = (p3_votes / role_votes) if role_votes else 0
            lines.append(f"- {role}: {p3_votes}/{role_votes} = {ratio:.1%}")

    lines.append("")
    lines.append("## Notes")
    lines.append("- This report is auto-generated from filenames + JSON result payload.")
    lines.append("- New trial files under the selected input directory will be included automatically next run.")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Analyze simulation JSON results")
    parser.add_argument("--input-dir", default="results_v2", help="Directory containing JSON result files")
    parser.add_argument("--output", default="analysis_summary.md", help="Output markdown file")
    args = parser.parse_args()

    paths = sorted(glob.glob(os.path.join(args.input_dir, "**", "*.json"), recursive=True))
    rows = []
    for p in paths:
        parsed = parse_result_file(p)
        if parsed is not None:
            rows.append(parsed)

    if not rows:
        raise SystemExit("No valid result JSON files found.")

    report = build_markdown(rows)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Wrote report: {os.path.abspath(args.output)}")
    print(f"Parsed trials: {len(rows)}")


if __name__ == "__main__":
    main()
