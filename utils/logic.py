# utils/logic.py
"""Pure helper logic (no Streamlit, no network) so it can be unit tested.

Everything that decides how issue records are interpreted lives here: null /
inconsistent value handling, department mapping, filtering, metrics and
validation of the automated analysis result.
"""

PRIORITIES = ["HIGH", "MEDIUM", "LOW"]
STATUS_OPTIONS = ["OPEN", "IN PROGRESS", "RESOLVED"]
UNASSIGNED = "Unassigned"

# Technicians are hardcoded; fetching them from the database would need a new
# table, which is intentionally not added (see README, "Optional extensions").
TECHNICIANS = ["Ali", "Ahmed", "Usman", "Hamza", UNASSIGNED]

# Maps the issue category to the responsible department. The department is
# stored on the issue when it is created.
DEPARTMENT_MAP = {
    "HVAC": "Facilities",
    "Electrical": "Electrical",
    "Plumbing": "Facilities",
    "IT": "IT",
    "Equipment": "Maintenance",
    "Furniture": "Facilities",
    "Safety": "Safety",
    "Other": "General Maintenance"
}
DEPARTMENT_LOOKUP = {k.lower(): v for k, v in DEPARTMENT_MAP.items()}
DEFAULT_DEPARTMENT = "General Maintenance"      # category exists but is not mapped
UNSPECIFIED_DEPARTMENT = "Unspecified"          # neither department nor category

_CANONICAL_DEPARTMENTS = {d.lower(): d for d in DEPARTMENT_MAP.values()}
_CANONICAL_CATEGORIES = {c.lower(): c for c in DEPARTMENT_MAP}
_CANONICAL_TECHNICIANS = {t.lower(): t for t in TECHNICIANS}
AI_FIELDS = ("category", "priority", "ai_summary", "suggested_action")


# ---------------------------------------------------------------------------
# Null / inconsistent value handling
# ---------------------------------------------------------------------------
def text(value) -> str:
    """Trimmed string; None becomes ''."""
    return "" if value is None else str(value).strip()


def norm(value) -> str:
    """Comparison key: trimmed, single-spaced, upper-case ('in_progress' -> 'IN PROGRESS')."""
    return " ".join(text(value).replace("_", " ").split()).upper()


def display_value(value, default="N/A"):
    """Return a safe value for display. NULL / empty values become the default.
    This only changes what is shown on screen, never the database."""
    if value is None or str(value).strip() == "":
        return default
    return value


def department_for_category(category) -> str:
    """Department used when an issue is saved (unknown categories -> General Maintenance)."""
    return DEPARTMENT_LOOKUP.get(text(category).lower(), DEFAULT_DEPARTMENT)


def resolve_department(issue) -> str:
    """Department shown / filtered / charted for an issue.

    Stored department first; older rows without one fall back to the category
    mapping so the same value is used everywhere. Display only, never written.
    """
    stored = text(issue.get("department"))
    if stored:
        return _CANONICAL_DEPARTMENTS.get(stored.lower(), stored)
    if text(issue.get("category")):
        return department_for_category(issue.get("category"))
    return UNSPECIFIED_DEPARTMENT


def resolve_technician(issue) -> str:
    tech = text(issue.get("assigned_to"))
    if not tech:
        return UNASSIGNED
    return _CANONICAL_TECHNICIANS.get(tech.lower(), tech)


def value_for(issue, field) -> str:
    """Normalised display value of a field used by filters, counts and tables."""
    if field == "department":
        return resolve_department(issue)
    if field == "assigned_to":
        return resolve_technician(issue)
    value = text(issue.get(field))
    if field in ("priority", "status"):
        value = norm(value)
    return value or "Unknown"


# ---------------------------------------------------------------------------
# Options, filtering, counting
# ---------------------------------------------------------------------------
def build_options(values, preferred=()):
    """Unique options (case/whitespace-insensitive). Preferred ones first, in order."""
    seen = {}
    for p in preferred:
        seen[norm(p)] = p
    extra = {}
    for v in values:
        key = norm(v)
        if key and key not in seen and key not in extra:
            extra[key] = text(v)
    return list(seen.values()) + sorted(extra.values(), key=str.lower)


def filter_options(issues, field, preferred=()):
    """Options for a filter drop-down: the preferred values plus any other value found in the records."""
    return build_options([value_for(i, field) for i in issues], preferred)


def ensure_option(options, current):
    """Make sure the current stored value is selectable. Returns (options, index)."""
    options = list(options)
    key = norm(current)
    for idx, opt in enumerate(options):
        if norm(opt) == key:
            return options, idx
    if key:
        options.insert(0, text(current))
        return options, 0
    return options, 0


def _is_all(value) -> bool:
    return value is None or text(value).lower() in ("", "all")


def issue_matches_search(issue, needle) -> bool:
    needle = text(needle).lower()
    if not needle:
        return True
    return any(
        needle in text(issue.get(field)).lower()
        for field in ("title", "description", "location")
    )


def filter_issues(issues, search="", category_filter="All", priority_filter="All",
                  status_filter="All", department_filter="All", technician_filter="All"):
    """Apply search + all filters together (every active condition must match)."""
    conditions = (
        ("category", category_filter),
        ("priority", priority_filter),
        ("status", status_filter),
        ("department", department_filter),
        ("assigned_to", technician_filter),
    )
    result = []
    for issue in issues:
        if not issue_matches_search(issue, search):
            continue
        if any(
            not _is_all(wanted) and norm(value_for(issue, field)) != norm(wanted)
            for field, wanted in conditions
        ):
            continue
        result.append(issue)
    return result


def count_by(issues, field, preferred=()):
    """Counts per value. Case variants are merged; known values keep their canonical
    spelling and order, other values follow."""
    counts, labels = {}, {norm(p): p for p in preferred}
    for issue in issues:
        value = value_for(issue, field)
        key = norm(value)
        labels.setdefault(key, value)
        counts[key] = counts.get(key, 0) + 1
    ordered = [norm(p) for p in preferred if norm(p) in counts]
    ordered += sorted((k for k in counts if k not in ordered), key=lambda k: (-counts[k], labels[k]))
    return {labels[k]: counts[k] for k in ordered}


def percent(part, total) -> int:
    return round(part / total * 100) if total else 0


def compute_metrics(issues) -> dict:
    """Headline numbers shared by the dashboard, sidebar and analytics page."""
    total = len(issues)
    resolved = sum(1 for i in issues if norm(i.get("status")) == "RESOLVED")
    high = sum(1 for i in issues if norm(i.get("priority")) == "HIGH")
    return {
        "total": total,
        "open": sum(1 for i in issues if norm(i.get("status")) == "OPEN"),
        "in_progress": sum(1 for i in issues if norm(i.get("status")) == "IN PROGRESS"),
        "resolved": resolved,
        "unresolved": total - resolved,
        "high": high,
        "unassigned": sum(1 for i in issues if resolve_technician(i) == UNASSIGNED),
        "resolution_rate": percent(resolved, total),
        "high_share": percent(high, total),
    }


# ---------------------------------------------------------------------------
# Validation of the automated analysis
# ---------------------------------------------------------------------------
class AIAnalysisError(ValueError):
    """The analysis response cannot be trusted, so the issue must not be saved as analysed."""


def validate_ai_result(result) -> dict:
    """Return a clean analysis dict or raise AIAnalysisError."""
    if isinstance(result, list) and len(result) == 1:
        result = result[0]
    if not isinstance(result, dict):
        raise AIAnalysisError("the analysis did not return the expected structure")

    missing = [f for f in AI_FIELDS if not text(result.get(f))]
    if missing:
        raise AIAnalysisError("the analysis is missing: " + ", ".join(missing))

    priority = norm(result["priority"])
    if priority not in PRIORITIES:
        raise AIAnalysisError(f"the analysis returned an unexpected priority ({text(result['priority'])!r})")

    category = text(result["category"])
    return {
        "category": _CANONICAL_CATEGORIES.get(category.lower(), category),
        "priority": priority,
        "ai_summary": text(result["ai_summary"]),
        "suggested_action": text(result["suggested_action"]),
    }
