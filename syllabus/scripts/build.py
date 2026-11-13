#!/usr/bin/env python3
"""Build the InLibrary syllabus catalog.

Source of truth: syllabus/data/<slug>.json (one file per plan) and syllabus/data/chips.json.

  python syllabus/scripts/build.py           validate, then regenerate v1/ and build-state.json
  python syllabus/scripts/build.py --check   validate only, write nothing

Generated, never edited by hand:
  v1/index.json           the list the app downloads and searches (published plans only)
  v1/plans/<slug>.json    one plan with its subjects and topics (published plans only)
  build-state.json        content hashes, used to bump a plan's version when its content changes

Everything under v1/ is read by installed apps. Fields may be added there, never removed,
renamed or retyped. No third-party packages needed (Python 3.10+).
"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT, STATE = ROOT / "data", ROOT / "v1", ROOT / "build-state.json"
CHIPS_FILE = DATA / "chips.json"
SCHEMA = 1

KINDS = {"school", "exam"}
CATEGORIES = {"entrance", "central-govt", "railways", "banking", "state-bihar", "state-other", "defence",
              "teaching", "school"}
PRIORITIES = {"high", "medium", "low"}
MODES = {"full", "revise_only"}
CHIP_GROUPS = ("school", "exams")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
BAD_DASHES = (chr(0x2013), chr(0x2014))


def write_json(path, obj):
    """Always LF, so the files are byte-identical on Windows, macOS and the CI runner."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------ load

def load_plans():
    """Returns (docs, load_errors). A file that is not valid JSON is an error, not a crash."""
    docs, errors = [], []
    for p in sorted(DATA.glob("*.json")):
        if p.name == CHIPS_FILE.name:
            continue
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"[{p.name}]: not valid JSON (line {e.lineno}, column {e.colno}): {e.msg}")
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("exam"), dict):
            errors.append(f"[{p.name}]: must be an object with an \"exam\" section")
            continue
        doc["_file"] = p.stem
        docs.append(doc)
    docs.sort(key=lambda d: (d["exam"].get("sort_order", 0), str(d["exam"].get("slug"))))
    return docs, errors


def load_chips():
    if not CHIPS_FILE.exists():
        return None, [f"[{CHIPS_FILE.name}]: file is missing"]
    try:
        return json.loads(CHIPS_FILE.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as e:
        return None, [f"[{CHIPS_FILE.name}]: not valid JSON (line {e.lineno}, column {e.colno}): {e.msg}"]


# ------------------------------------------------------------------ search (mirrors the app)

def search_words(entry):
    """Every word a query can match for one plan, lowercased."""
    parts = [entry.get(k) for k in ("name", "short_name", "name_hi", "class", "board", "stream")]
    parts += entry.get("aliases") or []
    words = []
    for part in parts:
        if part:
            words += re.split(r"[^\w+]+", str(part).lower())
    return [w for w in words if w]


def matches(entry, query):
    """True when every word of the query starts some word of the plan. The app uses the same rule."""
    words = search_words(entry)
    q = [w for w in re.split(r"[^\w+]+", query.lower()) if w]
    return bool(q) and all(any(w.startswith(x) for w in words) for x in q)


# ------------------------------------------------------------------ validation

def validate(docs, chips):
    errors, warnings = [], []
    seen = set()

    def err(where, msg):
        errors.append(f"{where}: {msg}")

    def scan_dashes(obj, where):
        if isinstance(obj, str):
            if any(d in obj for d in BAD_DASHES):
                err(where, f"contains an en/em dash, use '-' instead: {obj[:60]!r}")
        elif isinstance(obj, dict):
            for v in obj.values():
                scan_dashes(v, where)
        elif isinstance(obj, list):
            for v in obj:
                scan_dashes(v, where)

    for doc in docs:
        ex = doc["exam"]
        slug = ex.get("slug", "?")
        w = f"[{doc['_file']}.json]"
        scan_dashes({k: v for k, v in doc.items() if k != "_file"}, w)
        if not isinstance(slug, str) or not SLUG_RE.match(slug):
            err(w, "exam.slug must use lowercase letters, digits and hyphens only")
        elif slug != doc["_file"]:
            err(w, f"file name must match exam.slug ({slug!r})")
        if slug in seen:
            err(w, "duplicate exam.slug")
        seen.add(slug)
        for k in ("name", "short_name", "category"):
            if not ex.get(k):
                err(w, f"exam.{k} is required")
        if ex.get("category") not in CATEGORIES:
            err(w, f"unknown category {ex.get('category')!r}; use one of {sorted(CATEGORIES)}")
        if ex.get("kind") not in KINDS:
            err(w, "exam.kind must be \"school\" or \"exam\"")
        if ex.get("kind") == "school":
            for k in ("class", "board"):
                if not ex.get(k) or not isinstance(ex.get(k), str):
                    err(w, f"exam.{k} is required for a school plan, as text (class \"12\", board \"CBSE\")")
        aliases = ex.get("aliases")
        if not isinstance(aliases, list) or not aliases:
            err(w, "exam.aliases must be a non-empty list of the words students type")
        elif any(not isinstance(a, str) or not a.strip() or a != a.lower() for a in aliases):
            err(w, "every alias must be non-empty lowercase text")
        if not isinstance(ex.get("version"), int) or ex["version"] < 1:
            err(w, "exam.version must be an integer >= 1 (use 1 for a new plan)")
        for k in ("verified", "is_published"):
            if not isinstance(ex.get(k), bool):
                err(w, f"exam.{k} must be true or false")
        if ex.get("is_published") and not ex.get("verified"):
            warnings.append(f"{w} is published but verified is false")

        subjects = doc.get("subjects") or []
        if not subjects:
            err(w, "plan has no subjects")
        topic_slugs, subj_slugs, subj_orders, stages_used = {}, set(), set(), set()
        for s in subjects:
            sw = f"{w} subject {s.get('slug')}"
            if not SLUG_RE.match(s.get("slug") or ""):
                err(sw, "bad or missing subject slug")
            if s.get("slug") in subj_slugs:
                err(sw, "duplicate subject slug")
            subj_slugs.add(s.get("slug"))
            if not s.get("name"):
                err(sw, "subject name required")
            if not isinstance(s.get("sort_order"), int):
                err(sw, "sort_order must be an integer")
            elif s["sort_order"] in subj_orders:
                err(sw, f"sort_order {s['sort_order']} used twice in this plan")
            subj_orders.add(s.get("sort_order"))
            topics = s.get("topics") or []
            if not topics:
                err(sw, "subject has no topics")
            orders = set()
            for t in topics:
                tw = f"{sw} topic {t.get('slug')}"
                if not SLUG_RE.match(t.get("slug") or ""):
                    err(tw, "bad or missing topic slug")
                if t.get("slug") in topic_slugs:
                    err(tw, "duplicate topic slug in this plan")
                topic_slugs[t.get("slug")] = t
                if not t.get("name"):
                    err(tw, "topic name required")
                if not isinstance(t.get("sort_order"), int):
                    err(tw, "sort_order must be an integer")
                elif t["sort_order"] in orders:
                    err(tw, f"sort_order {t['sort_order']} used twice in this subject")
                orders.add(t.get("sort_order"))
                # Scheduler fields are optional; when present they must be sane.
                if t.get("est_hours") is not None:
                    h = t["est_hours"]
                    if not isinstance(h, (int, float)) or h <= 0 or h > 40:
                        err(tw, f"est_hours must be > 0 and <= 40 (got {h!r})")
                if t.get("priority") is not None and t["priority"] not in PRIORITIES:
                    err(tw, f"priority must be high/medium/low (got {t.get('priority')!r})")
                if t.get("stage"):
                    stages_used.add(t["stage"])
        for ts, t in topic_slugs.items():
            if t.get("prereq") and t["prereq"] not in topic_slugs:
                err(f"{w} topic {ts}", f"prereq {t['prereq']!r} not found")
        for ts in topic_slugs:
            visited, cur = set(), ts
            while cur and cur in topic_slugs:
                if cur in visited:
                    err(f"{w} topic {ts}", "prerequisite cycle")
                    break
                visited.add(cur)
                cur = topic_slugs[cur].get("prereq")

        # Plan templates are optional (the app does not use them yet); validated when present.
        templates = doc.get("templates") or []
        if templates and sum(1 for t in templates if t.get("is_default")) != 1:
            err(w, "exactly one template must have is_default=true")
        tslugs = set()
        for tp in templates:
            pw = f"{w} template {tp.get('slug')}"
            if not SLUG_RE.match(tp.get("slug") or "") or tp.get("slug") in tslugs:
                err(pw, "bad or duplicate template slug")
            tslugs.add(tp.get("slug"))
            r = tp.get("rules") or {}
            ph = r.get("phases") or {}
            total = sum(ph.get(k, 0) for k in ("learn", "revise", "mock"))
            if abs(total - 1.0) > 0.01:
                err(pw, f"phases must add up to 1.0 (got {total})")
            if r.get("mode") not in MODES:
                err(pw, f"mode must be one of {sorted(MODES)}")
            if not r.get("include_priorities") or set(r["include_priorities"]) - PRIORITIES:
                err(pw, "include_priorities must be a non-empty subset of high/medium/low")
            if not isinstance(tp.get("version"), int) or tp["version"] < 1:
                err(pw, "template version must be an integer >= 1")

    # Chips: every chip must find at least one published plan, or the student taps into nothing.
    if chips is not None:
        cw = f"[{CHIPS_FILE.name}]"
        published = [index_entry(d) for d in docs if d["exam"].get("is_published") is True]
        if not isinstance(chips, dict) or set(chips) != set(CHIP_GROUPS):
            err(cw, f"must have exactly the lists {list(CHIP_GROUPS)}")
        else:
            for group in CHIP_GROUPS:
                if not isinstance(chips[group], list) or not chips[group]:
                    err(cw, f"{group} must be a non-empty list")
                    continue
                for chip in chips[group]:
                    label = chip.get("label") if isinstance(chip, dict) else None
                    query = chip.get("query") if isinstance(chip, dict) else None
                    if not label or not query:
                        err(cw, f"{group}: every chip needs a label and a query")
                    elif not any(matches(p, query) for p in published):
                        err(cw, f"{group} chip {label!r}: query {query!r} finds no published plan")
    return errors, warnings


# ------------------------------------------------------------------ versioning

def content_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def plan_hash(doc):
    ex = {k: v for k, v in doc["exam"].items() if k not in ("version", "last_verified")}
    return content_hash({"exam": ex, "subjects": doc["subjects"], "templates": doc.get("templates") or []})


def source_doc(doc):
    return {k: v for k, v in doc.items() if k != "_file"}


def bump_versions(docs):
    """Raises a plan's version when its content changed since the last build."""
    prev = json.loads(STATE.read_text(encoding="utf-8")).get("plans", {}) if STATE.exists() else {}
    bumped = []
    for doc in docs:
        ex = doc["exam"]
        p = prev.get(ex["slug"])
        if p and plan_hash(doc) != p["hash"] and ex["version"] <= p["version"]:
            ex["version"] = p["version"] + 1
            write_json(DATA / (ex["slug"] + ".json"), source_doc(doc))
            bumped.append(f"{ex['slug']} -> v{ex['version']}")
    return bumped


# ------------------------------------------------------------------ outputs

def index_entry(doc):
    ex = doc["exam"]
    subjects = doc.get("subjects") or []
    entry = {"slug": ex.get("slug"), "kind": ex.get("kind"), "name": ex.get("name"), "short_name": ex.get("short_name")}
    for k in ("name_hi", "class", "board", "stream"):
        if ex.get(k):
            entry[k] = ex[k]
    entry.update({
        "aliases": ex.get("aliases") or [],
        "category": ex.get("category"),
        "subject_count": len(subjects),
        "topic_count": sum(len(s.get("topics") or []) for s in subjects),
        "version": ex.get("version"),
    })
    return entry


def named(item):
    out = {"slug": item["slug"], "name": item["name"]}
    if item.get("name_hi"):
        out["name_hi"] = item["name_hi"]
    out["sort_order"] = item["sort_order"]
    return out


def plan_file(doc):
    out = {"schema": SCHEMA, **index_entry(doc), "subjects": []}
    for s in sorted(doc["subjects"], key=lambda x: x["sort_order"]):
        subject = named(s)
        subject["topics"] = [named(t) for t in sorted(s["topics"], key=lambda x: x["sort_order"])]
        out["subjects"].append(subject)
    return out


def write_outputs(docs, chips):
    published = [d for d in docs if d["exam"]["is_published"]]
    if OUT.exists():
        shutil.rmtree(OUT)
    for doc in published:
        write_json(OUT / "plans" / (doc["exam"]["slug"] + ".json"), plan_file(doc))
    write_json(OUT / "index.json", {"schema": SCHEMA, "chips": chips, "plans": [index_entry(d) for d in published]})
    write_json(STATE, {
        "generated_by": "syllabus/scripts/build.py",
        "plans": {d["exam"]["slug"]: {"hash": plan_hash(d), "version": d["exam"]["version"]} for d in docs},
    })
    return published


# ------------------------------------------------------------------ main

def main():
    args = set(sys.argv[1:])
    docs, errors = load_plans()
    chips, chip_errors = load_chips()
    errors += chip_errors
    more, warnings = validate(docs, chips)
    errors += more
    for w in warnings:
        print("warning:", w)
    if errors:
        for e in errors:
            print("ERROR:", e)
        sys.exit(f"{len(errors)} error(s); nothing written")
    if "--check" in args:
        print(f"OK: {len(docs)} plans valid")
        return
    bumped = bump_versions(docs)
    published = write_outputs(docs, chips)
    n_topics = sum(len(s["topics"]) for d in published for s in d["subjects"])
    print(f"OK: {len(docs)} plans, {len(published)} published, {n_topics} published topics -> v1/")
    for b in bumped:
        print("version bumped:", b)


if __name__ == "__main__":
    main()
