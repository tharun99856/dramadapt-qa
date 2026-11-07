"""Phase 0 Step D scoring. All numbers here come from the reviewer's own annotation file."""

from __future__ import annotations

CHECK_TO_TYPE = {"meaning": "meaning", "relationship": "relationship", "timing": "timing",
                 "naturalness": "naturalness", "script": "script"}
SEVERITY_LEVELS = ["low", "medium", "high"]


def human_issues(annotations: dict[str, dict], expand=None) -> dict[str, set[str]]:
    """line_id -> set of error types the reviewer confirmed. Unfilled rows are reported, not guessed."""
    out: dict[str, set[str]] = {}
    for line_id, row in annotations.items():
        verdict = (row.get("verdict") or "").strip().lower()
        if verdict in ("needs_revision", "needs revision", "revise"):
            types = {t.strip().lower() for t in re_types(row.get("error_types")) if t.strip()}
            out[line_id] = types or {"unspecified"}
    return out


def re_types(value) -> list[str]:
    text = (value or "").strip()
    if not text:
        return []
    for sep in (";", ",", "|", "/"):
        if sep in text:
            return text.split(sep)
    return text.split()


def unfilled(annotations: dict[str, dict]) -> list[str]:
    return [lid for lid, row in annotations.items() if not (row.get("verdict") or "").strip()]


def ambiguous(annotations: dict[str, dict]) -> list[str]:
    return [
        lid
        for lid, row in annotations.items()
        if (row.get("verdict") or "").strip().lower() not in ("acceptable", "needs_revision", "needs revision", "revise", "ok")
        and (row.get("verdict") or "").strip()
    ]


def _matches(flag_type: str, human_types: set[str]) -> bool:
    if flag_type == "baseline":
        return bool(human_types)
    return flag_type in human_types


def score(flags: list[dict], issues: dict[str, set[str]], chains: dict[str, list[str]] | None = None) -> dict:
    """Precision/recall for one system's flag list.

    Recall here is instance-based on purpose. The first version of this function divided a flag
    count by a flag count plus an instance count, which made the two arms uncomparable: the
    baseline names no error type, so its `tp + fn` came to 210 against 158 real reviewer
    instances and its recall read 0.248 when it actually touches 0.690 of the sheet. Numerator
    and denominator are now the same kind of thing - distinct reviewer (line, type) instances -
    and `line_level` is reported next to it because "will the director see this line" is the
    operational question and "did it name the type" is not.
    """
    chains = chains or {}
    flagged_ids = {f["line_id"] for f in flags}
    all_instances = {(lid, t) for lid, ts in issues.items() for t in ts}
    tp = fp = 0
    tp_lines: list[str] = []
    fp_lines: list[str] = []
    chain_helps = 0
    credited: set[tuple[str, str]] = set()
    for flag in flags:
        line_id = flag["line_id"]
        ftype = CHECK_TO_TYPE.get(flag["check"], flag["check"])
        human = issues.get(line_id)
        direct = bool(human) and _matches(ftype, human or set())
        partner: str | None = None
        if not direct and flag["check"] in ("meaning", "relationship"):
            for cid, members in chains.items():
                if line_id in members:
                    hit = next((o for o in members if o != line_id and o in issues
                                and _matches(ftype, issues[o])), None)
                    if hit:
                        partner = hit
                        break
        if direct or partner:
            tp += 1
            tp_lines.append(line_id)
            if partner:
                chain_helps += 1
                human = issues.get(partner)
                line_id = partner
            if human:
                if ftype == "baseline":
                    credited.update((line_id, t) for t in human)
                elif ftype in human:
                    credited.add((line_id, ftype))
        else:
            fp += 1
            fp_lines.append(line_id)

    uncredited = all_instances - credited
    fn = len(uncredited)
    found = len(credited)
    issue_lines = set(issues)
    lines_found = len(flagged_ids & issue_lines)
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = found / len(all_instances) if all_instances else None
    # kept only so the change is auditable against the previously submitted numbers
    legacy_fn = 0
    for line_id, types in issues.items():
        if line_id in flagged_ids:
            legacy_fn += sum(1 for ftype in types
                             if not any(f["line_id"] == line_id
                                        and CHECK_TO_TYPE.get(f["check"], f["check"]) == ftype for f in flags))
        else:
            legacy_fn += len(types)
    legacy_denom = tp + legacy_fn
    return {
        "flags": len(flags),
        "lines_flagged": len(flagged_ids),
        "true_positive_flags": tp,
        "false_positive_flags": fp,
        "instances_found": found,
        "instances_total": len(all_instances),
        "missed_human_issues": fn,
        "precision": round(precision, 3) if precision is not None else None,
        "recall": round(recall, 3) if recall is not None else None,
        "recall_note": "instances credited / reviewer instances; numerator and denominator are the same kind",
        "recall_legacy_flagcount": round(tp / legacy_denom, 3) if legacy_denom else None,
        "legacy_denominator_was": legacy_denom,
        "line_level": {
            "issue_lines_found": lines_found,
            "issue_lines_total": len(issue_lines),
            "recall": round(lines_found / len(issue_lines), 3) if issue_lines else None,
            "precision": round(lines_found / len(flagged_ids), 3) if flagged_ids else None,
        },
        "tp_line_ids": sorted(set(tp_lines)),
        "fp_line_ids": sorted(set(fp_lines)),
        "missed": sorted(uncredited),
        "credited_instances": sorted(credited),
        "flags_rescued_by_chain_matching": chain_helps,
    }


def per_check(flags: list[dict], issues: dict[str, set[str]], chains=None) -> dict:
    """Per-check scores.

    Plain `recall` is measured against every reviewer instance so the checks stay comparable with
    the overall figure, which makes a check that is near perfect at its own job look weak. So
    `type_recall` comes with it: of the instances the reviewer labelled with this type, how many
    did this check's flags credit.
    """
    out = {}
    for check in sorted({f["check"] for f in flags}):
        subset = [f for f in flags if f["check"] == check]
        res = score(subset, issues, chains)
        n_type = sum(1 for lid, ts in issues.items() for t in ts if t == check)
        of_type = sum(1 for _lid, t in res["credited_instances"] if t == check)
        res["type_instances_total"] = n_type
        res["type_instances_found"] = of_type
        res["type_recall"] = round(of_type / n_type, 3) if n_type else None
        out[check] = res
    return out


def severity_sweep(flags: list[dict], issues: dict[str, set[str]], chains=None) -> list[dict]:
    """Keep only flags at or above each severity, so two systems can be compared at similar precision."""
    points = []
    for cutoff in reversed(SEVERITY_LEVELS):
        keep = [f for f in flags if SEVERITY_LEVELS.index(f.get("severity", "low")) >= SEVERITY_LEVELS.index(cutoff)]
        res = score(keep, issues, chains)
        points.append({"at_least": cutoff, "flags": res["flags"], "precision": res["precision"], "recall": res["recall"]})
    return points


def best_recall_at_precision(points: list[dict], target_precision: float | None) -> dict:
    if target_precision is None or not points:
        return {"available": False, "reason": "the other system produced no measurable precision"}
    eligible = [p for p in points if p["precision"] is not None and p["precision"] >= target_precision]
    if not eligible:
        return {"available": False, "target_precision": target_precision,
                "reason": "no severity cut reaches that precision", "points": points}
    best = max(eligible, key=lambda p: (p["recall"] if p["recall"] is not None else -1))
    return {"available": True, "target_precision": target_precision, "at_least": best["at_least"],
            "precision": best["precision"], "recall": best["recall"], "flags": best["flags"]}


def acceptance_rates(decisions: dict[tuple[str, str], dict]) -> dict:
    """Reviewer acceptance rate per check: accept, accept-but-modify, dismiss."""
    buckets: dict[str, dict[str, int]] = {}
    for (_flag_id, _line), row in decisions.items():
        check = (row.get("check") or "?").strip()
        status = (row.get("status") or "pending").strip().lower()
        b = buckets.setdefault(check, {"accept": 0, "accept_but_modify": 0, "dismiss": 0, "pending": 0})
        if status in ("accepted", "accept", "approved"):
            b["accept"] += 1
        elif status in ("edited", "accept_but_modify", "modified"):
            b["accept_but_modify"] += 1
        elif status in ("dismissed", "dismiss", "rejected"):
            b["dismiss"] += 1
        else:
            b["pending"] += 1
    out = {}
    for check, b in sorted(buckets.items()):
        acted = b["accept"] + b["accept_but_modify"] + b["dismiss"]
        out[check] = {
            **b,
            "decisions_recorded": acted,
            "acceptance_rate": round((b["accept"] + b["accept_but_modify"]) / acted, 3) if acted else None,
            "modify_share": round(b["accept_but_modify"] / acted, 3) if acted else None,
            "dismissal_rate": round(b["dismiss"] / acted, 3) if acted else None,
        }
    return out


def seeded_recall(seed_manifest: dict, flags: list[dict]) -> dict:
    """Did the check that was supposed to catch a seeded error actually catch it?

    The first version counted a seeded line as detected if *any* flag landed on it, which let a
    meaning seed score as a hit when only the timing check spoke. Both readings are reported now,
    because the gap between them is itself a result.
    """
    out: dict[str, dict] = {}
    for edit in seed_manifest.get("edits", []):
        expected = edit["expected_check"]
        row = out.setdefault(expected, {"seeded": 0, "detected_by_expected_check": 0,
                                        "detected_by_any_check": 0, "by_check": {}, "lines": []})
        row["seeded"] += 1
        hits = [f for f in flags if f["line_id"] == edit["line_id"]]
        right = [f for f in hits if f["check"] == expected]
        if hits:
            row["detected_by_any_check"] += 1
            for f in hits:
                row["by_check"][f["check"]] = row["by_check"].get(f["check"], 0) + 1
        if right:
            row["detected_by_expected_check"] += 1
        else:
            row["lines"].append({"line_id": edit["line_id"], "op": edit.get("op"),
                                 "fired_instead": sorted({f["check"] for f in hits})})
    for row in out.values():
        row["recall"] = (round(row["detected_by_expected_check"] / row["seeded"], 3)
                         if row["seeded"] else None)
        row["recall_any_check"] = (round(row["detected_by_any_check"] / row["seeded"], 3)
                                   if row["seeded"] else None)
        row["lines"] = sorted(row["lines"], key=lambda r: r["line_id"])
    return out
