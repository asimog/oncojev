"""Phase 8: the frontend is presentation-only with distinct epistemic categories."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"

FRONTEND_SOURCES = tuple((WEB / "app").rglob("*.tsx")) + tuple((WEB / "lib").rglob("*.ts"))

FORBIDDEN_BACKEND_TOKENS = (
    "admit_scientific_evidence",
    "FrontierPolicy",
    "run_cycle",
    "ScienceExecutor",
    "src.persistence",
    "src.science",
    "src.runtime",
)


def test_frontend_contains_no_orchestration_or_scientific_logic():
    for path in FRONTEND_SOURCES:
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_BACKEND_TOKENS:
            assert token not in text, f"{token} leaked into {path.relative_to(ROOT)}"


def test_frontend_distinguishes_all_epistemic_categories():
    categories = (WEB / "lib/categories.ts").read_text(encoding="utf-8")
    styles = (WEB / "app/globals.css").read_text(encoding="utf-8")
    for category in ("observation", "measurement", "evidence", "jev", "hypothesis", "action"):
        assert f"{category}:" in categories
        assert f".cat-{category}" in styles
        assert f".badge-{category}" in styles


def test_frontend_reads_live_api_with_offline_snapshot_fallback():
    snapshot = (WEB / "lib/snapshot.ts").read_text(encoding="utf-8")
    assert "@/data/snapshot.json" in snapshot
    assert "ONCOJEV_API_URL" in snapshot
    assert 'cache: "no-store"' in snapshot
    assert (WEB / "app/page.tsx").exists()
    assert any((WEB / "app/blocks").glob("*/page.tsx"))
