"""Reference adapter: the shared-board execution plane + solo session CLI.

This is the implementation the STL trust-layer specs were extracted from, so it
is the natural first subject — and, per the P3 gate decision, the one whose
conformance must be published honestly before any reference implementation ships.
"""
from __future__ import annotations
import json, os, re, subprocess, time, urllib.request, urllib.error
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from stlconf import Adapter, Capability

# Deployment-specific locations. Configure via environment; nothing here is
# baked to one machine (a published kit must not carry its author's paths).
#   STLCONF_API         board execution-plane base URL
#   STLCONF_BOARDS_DIR  directory holding authored .stl board sources
#   STLCONF_SOLO_HOME   session/marker root for the solo session CLI
API = os.environ.get("STLCONF_API", "http://127.0.0.1:8800")
BOARDS = Path(os.environ.get("STLCONF_BOARDS_DIR",
                             Path.home() / "repos/shared-board/data/boards")).expanduser()
# NOTE: the derived-JSON directory is deliberately NOT exposed as a constant.
# Reaching into data/.json/ directly is exactly what stranded 276 snapshots;
# board removal goes through teardown_board() -> DELETE /api/boards/<id>.
_SOLO = Path(os.environ.get("STLCONF_SOLO_HOME", Path.home() / ".solo")).expanduser()
SESSIONS = _SOLO / "sessions"
SIGNALS = _SOLO / "signals"


def _http(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode() or "{}")


def teardown_board(board_id, archive_dir=None):
    """Remove a fixture board through the implementation's OWN delete path.

    A board exists as TWO files: the derived JSON (data/.json/<id>.json) and a
    snapshot (data/snapshots/<category>/<slug>.stl). Only DELETE /api/boards/<id>
    handles both -- it archives the JSON reversibly and lets the server clear the
    snapshot via _refresh_group. Moving the JSON directly (what this kit did until
    2026-09-06) deletes one half and strands the other: 276 orphaned kitfixture
    snapshots accumulated from 09-02, found by another line's orphan scan.
    Verified 2026-09-06 on a throwaway board: 200 + archived_to, JSON archived,
    snapshot cleared, source .stl left behind, second DELETE returns 404.

    DELETE does NOT remove the authored source, so a fixture that wrote a .stl must
    also clear that side or the next GET /api/boards re-materializes the board.
    The source is archived rather than deleted, keeping teardown reversible (§4.5).
    """
    try:
        _http("DELETE", f"/api/boards/{board_id}")
    except urllib.error.HTTPError as e:
        if e.code != 404:                      # 404 = already gone; teardown is idempotent
            raise
    src = BOARDS / f"{board_id}.stl"
    if src.exists():
        if archive_dir is not None:
            archive_dir.mkdir(parents=True, exist_ok=True)
            src.rename(archive_dir / src.name)
        else:
            src.unlink()


def _sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


class SharedBoardSolo(Adapter):
    name = "shared-board+solo (reference implementation)"
    capabilities = {Capability.BOARD_CRUD, Capability.CURSOR,
                    Capability.DETECTORS, Capability.LIFECYCLE, Capability.VERDICTS,
                    Capability.INTENT}

    def __init__(self):
        self._stamp = time.strftime("%Y%m%d-%H%M%S")
        self._made: list[str] = []

    # ---- BOARD_CRUD ----
    def create_board(self, board_id, tasks):
        anchor = "Zz" + re.sub(r"[^A-Za-z0-9]", "", board_id.title())[:28]
        lines = [f'[Board:{anchor}] -> [Meta] ::mod(title="STLCONF FIXTURE {board_id}", '
                 f'category="kitfixture", created_by="stlconf")']
        for i, t in enumerate(tasks, 1):
            lines.append(f'[Board:{anchor}] -> [T{i}] ::mod(type="checkbox", content="{t}")')
        (BOARDS / f"{board_id}.stl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        self._made.append(board_id)
        _http("GET", "/api/boards")            # materialize
        return board_id

    def create_board_raw(self, board_id, stl_text):
        """Author a board from raw STL — lets checks submit deliberately malformed
        sources (e.g. carrying execution state) to test that they are refused."""
        (BOARDS / f"{board_id}.stl").write_text(stl_text, encoding="utf-8")
        self._made.append(board_id)
        _http("GET", "/api/boards")
        return board_id

    def raw_items(self, board_id):
        """All items including notes (items() filters to checkboxes)."""
        return _http("GET", f"/api/boards/{board_id}")["items"]

    def cursor_info(self, board_id):
        """Whatever the execution plane reports about the cursor, verbatim."""
        b = _http("GET", f"/api/boards/{board_id}")
        its = [i for i in b["items"] if i.get("type") == "checkbox"]
        cur = [i for i in its if i.get("status") == "in_progress"]
        return {"cursor": cur[0]["content"] if cur else None,
                "board_keys": sorted(b.keys()),
                "cause_field_present": any(k for k in b if "cursor" in k.lower() or "cause" in k.lower())}

    def items(self, board_id):
        b = _http("GET", f"/api/boards/{board_id}")
        return [i for i in b["items"] if i.get("type") == "checkbox"]

    def set_status(self, board_id, item_id, status, sub_status=None):
        body = {"status": status, "updated_by": "stlconf"}
        if sub_status:
            body["sub_status"] = sub_status
        return _http("PUT", f"/api/boards/{board_id}/items/{item_id}", body)

    def archive_board(self, board_id):
        teardown_board(board_id, BOARDS / "ARCHIVED" / f"stlconf-{self._stamp}")

    # ---- BOARD_CRUD: retirement surface (C10) ----
    def board_summary(self, board_id):
        """The board's own record, including the implementation's retirement marker."""
        return _http("GET", f"/api/boards/{board_id}")

    def is_listed(self, board_id):
        return any(isinstance(b, dict) and b.get("id") == board_id
                   for b in _http("GET", "/api/boards"))

    def set_retired(self, board_id, retired: bool):
        """Drive the implementation's OWN retire/restore path (not the kit's file move)."""
        return _http("PUT", f"/api/boards/{board_id}", {"archived": bool(retired)})

    # ---- CURSOR ----
    def append_structure(self, board_id, task):
        src = BOARDS / f"{board_id}.stl"
        anchor = re.search(r"\[Board:(\w+)\]", src.read_text(encoding="utf-8")).group(1)
        with src.open("a", encoding="utf-8") as f:
            f.write(f'[Board:{anchor}] -> [TAppend] ::mod(type="checkbox", content="{task}")\n')
        _http("GET", "/api/boards")            # re-materialize

    def cursor(self, board_id):
        for i in self.items(board_id):
            if i.get("status") == "in_progress":
                return i["content"]
        return None

    # ---- DETECTORS ----
    def detectors(self):
        out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
        return [l for l in out.splitlines() if "_signal-check" in l and "ps -eo" not in l]

    def wake_notifications(self):
        sess = os.environ.get("STLCONF_SESSION")
        if not sess:
            return None                      # unconfigured -> honest skip, never a guess
        p = SIGNALS / f"{sess}.wake"
        if not p.is_file():
            return None
        return p.read_text(errors="replace").splitlines()

    # ---- LIFECYCLE ----
    def session_init(self, name, board_id): _sh(f"solo init {name} --board {board_id}")
    def session_pause(self, name):          _sh(f"solo pause-cycle {name}")
    def session_destroy(self, name):        _sh(f"solo done {name}")

    def session_autoresume(self, name):
        p = SESSIONS / f"{name}.json"
        return json.loads(p.read_text()).get("auto_resume") if p.exists() else None

    # ---- INTENT ----
    def intent_records(self):
        out = []
        for p in BOARDS.glob("*.stl"):
            for m in re.finditer(r"intent:\s*([^\"\n]{10,600})", p.read_text(errors="replace")):
                out.append(m.group(1).strip())
        return out

    def reinstantiated_plans(self):
        """Boards declaring themselves a T1 re-instantiation of a predecessor."""
        out = []
        for p in BOARDS.glob("*.stl"):
            t = p.read_text(errors="replace")
            m = re.search(r'(intent_of|supersedes)="([^"]+)"', t)
            if m:
                out.append({"board": p.stem, "field": m.group(1), "predecessor": m.group(2)})
        return out

    def create_child_board(self, board_id, parent_id, parent_item, tasks):
        anchor = "Zz" + re.sub(r"[^A-Za-z0-9]", "", board_id.title())[:28]
        lines = [f'[Board:{anchor}] -> [Meta] ::mod(title="STLCONF CHILD {board_id}", '
                 f'category="kitfixture", created_by="stlconf", '
                 f'parent_board="{parent_id}", parent_item="{parent_item}")']
        for i, t in enumerate(tasks, 1):
            lines.append(f'[Board:{anchor}] -> [C{i}] ::mod(type="checkbox", content="{t}")')
        (BOARDS / f"{board_id}.stl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        self._made.append(board_id)
        _http("GET", "/api/boards")
        return board_id

    # ---- VERDICTS ----
    def verdict_records(self, board_ids=None, limit=40):
        """Read outcome records written by the execution plane.

        NOTE: GET /api/boards returns SUMMARIES with no `items` key. Iterating it
        looking for notes yields a silent zero (measured 2026-09-02 while building
        this adapter). Records live only on the per-board endpoint.
        """
        if board_ids is None:
            summaries = [b for b in _http("GET", "/api/boards") if isinstance(b, dict)]
            summaries.sort(key=lambda b: b.get("updated_at") or "", reverse=True)
            board_ids = [b["id"] for b in summaries[:limit]]
        recs = []
        for bid in board_ids:
            try:
                b = _http("GET", f"/api/boards/{bid}")
            except Exception:
                continue
            for it in b.get("items", []):
                n = it.get("notes") or ""
                # A standing item accumulates MANY tick records in one notes blob
                # (Board-as-Spec C15). One notes field != one record; splitting on the
                # record boundary is required or per-record checks mis-count (measured
                # 2026-09-02: a 9-tick blob read as one record with 9 provenance values).
                for part in re.split(r"(?=\[Verdict:)", n):
                    if 'role="verdict"' in part or 'role="conformance_verdict"' in part:
                        recs.append(part)
        return recs
