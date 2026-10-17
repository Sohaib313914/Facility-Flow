"""In-memory stand-ins for Supabase and Gemini so tests never need credentials."""
import copy
import sys
import types
from datetime import datetime, timedelta, timezone


def _ts(days_ago):
    return (datetime(2026, 10, 13, 10, 5, tzinfo=timezone.utc) - timedelta(days=days_ago)).isoformat()


SEED = [
    dict(id=1, title="AC not working", description="Not cooling.\nStarted yesterday.", location="Lab 3", category="HVAC", priority="HIGH", department="Facilities", status="OPEN", assigned_to=None, ai_summary="AC fails to cool.", suggested_action="Check refrigerant.", created_at=_ts(0)),
    dict(id=2, title="Flickering <b>lights</b>", description="x <script>alert(1)</script>", location="Block B", category="Electrical", priority="MEDIUM", department="Electrical", status="IN PROGRESS", assigned_to="Ali", ai_summary="Lighting issue.", suggested_action="Inspect wiring.", created_at=_ts(1)),
    dict(id=3, title="Leaking tap", description="Drips", location="Washroom 2", category="Plumbing", priority="LOW", department="Facilities", status="RESOLVED", assigned_to="Usman", ai_summary="Minor leak.", suggested_action="Replace washer.", created_at=_ts(2)),
    dict(id=4, title="Projector dead", description=None, location=None, category=None, priority="MEDIUM", department=None, status="OPEN", assigned_to="Zed", ai_summary=None, suggested_action=None, created_at=None),
    dict(id=5, title="Wifi down", description="No internet", location="Library", category="IT", priority="HIGH", department="IT", status="OPEN", assigned_to="Hamza", ai_summary="Outage.", suggested_action="Restart AP.", created_at=_ts(3)),
]


class Resp:
    def __init__(self, data):
        self.data = data


class Query:
    def __init__(self, store):
        self.store, self.op, self.filters, self.payload, self.order_by = store, None, [], None, None

    def select(self, cols="*"): self.op = "select"; return self
    def order(self, col, desc=False): self.order_by = (col, desc); return self
    def eq(self, k, v): self.filters.append((k, v)); return self
    def insert(self, row): self.op, self.payload = "insert", row; return self
    def update(self, row): self.op, self.payload = "update", row; return self

    def execute(self):
        failure = self.store.fail.get(self.op)
        if failure is not None:
            raise failure
        rows = self.store.rows
        if self.op == "insert":
            row = dict(self.payload, id=self.store.next_id, created_at=datetime.now(timezone.utc).isoformat())
            row.setdefault("assigned_to", None)
            self.store.next_id += 1
            rows.insert(0, row)
            return Resp([row])
        sel = [r for r in rows if all(r.get(k) == v for k, v in self.filters)]
        if self.op == "update":
            for r in sel:
                r.update(self.payload)
            return Resp(sel)
        if self.order_by:
            col, desc = self.order_by
            sel = sorted(sel, key=lambda r: (r.get(col) is not None, r.get(col) or ""), reverse=desc)
        return Resp(copy.deepcopy(sel))


class Store:
    def __init__(self):
        self.rows = copy.deepcopy(SEED)
        self.next_id = 100
        self.fail = {}  # e.g. {"update": RuntimeError("db down")} makes that operation raise

    def table(self, name):
        return Query(self)


def install():
    """Put fake `services.database` / `services.ai_service` into sys.modules; return the store."""
    store = Store()
    pkg = types.ModuleType("services"); pkg.__path__ = []
    db = types.ModuleType("services.database"); db.supabase = store
    ai = types.ModuleType("services.ai_service")
    ai.MODEL = "gemini-3.5-flash-lite"
    ai.calls = []

    def analyze_issue(title, description):
        ai.calls.append((title, description))
        return {"category": "HVAC", "priority": "HIGH", "ai_summary": f"Summary: {title}", "suggested_action": "Send a technician."}

    ai.analyze_issue = analyze_issue
    for name, mod in (("services", pkg), ("services.database", db), ("services.ai_service", ai)):
        sys.modules[name] = mod
    pkg.database, pkg.ai_service = db, ai
    return store, ai
