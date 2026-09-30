"""Tests that guard the claims the demo depends on."""

from __future__ import annotations

from charterplanner import data as _data
from charterplanner import optimizer as _opt
from charterplanner import pipeline as _pl


def test_plan_verifies_and_is_feasible():
    sc = _data.build_scenario(seed=3, weeks=12)
    plan = _opt.optimize(sc, time_limit=10.0)
    v = _opt.verify(sc, plan)
    assert v.ok, v.violations
    for a in plan.assignments:
        port = sc.port(a.port_id)
        vessel = sc.vessel(a.vessel_id)
        assert vessel.draft_m <= port.max_draft_m
        assert a.arrive_week <= sc.parcel(a.parcel_id).required_by_week


def test_optimiser_beats_or_matches_spot():
    sc = _data.build_scenario(seed=3, weeks=12)
    plan = _opt.optimize(sc, time_limit=10.0)
    spot = _opt.spot_baseline(sc)
    assert plan.total_cost <= spot.total_cost
    assert plan.voyages_used <= spot.voyages_used


def test_all_feasible_cargo_served():
    sc = _data.build_scenario(seed=3, weeks=12)
    assert _opt.optimize(sc, time_limit=10.0).unserved == []


def test_report_shape_and_market():
    r = _pl.run(seed=1, weeks=12)
    for key in ("metrics", "plan", "baseline", "forecast", "verification", "scenario", "market", "audit"):
        assert key in r
    assert r["metrics"]["cost_saved_pct"] >= 0
    assert r["verification"]["ok"]
    assert r["market"]["BDI"] == 3178 and r["market"]["date"] == "2026-09-29"
    assert r["baseline"]["voyages"]  # spot plan detail is present


def test_eval_positive_and_on_time():
    r = _pl.run_eval(seeds=8, weeks=12)
    assert r["all_verified"]
    assert r["cost_saved_pct"][0] > 0
    assert r["on_time_pct"][0] == 100.0


def test_manual_add_and_cancel(tmp_path, monkeypatch):
    import charterplanner.requests_store as st
    for attr, name in [("_ADD", "a"), ("_CANCEL", "c"), ("_RESCHED", "r"), ("_REROUTE", "x")]:
        monkeypatch.setattr(st, attr, tmp_path / (name + ".jsonl"))
    base = _pl.run(seed=3, weeks=12)
    n = base["metrics"]["total_parcels"]
    st.record_addition({"commodity": "Coking coal", "origin": "AUS", "port": "GGV",
                        "volume_t": 68000, "required_by_week": 9, "priority": 5})
    added = _pl.run(seed=3, weeks=12)
    assert added["metrics"]["total_parcels"] == n + 1 and added["manual_ids"] == ["CR-001"]
    st.record_cancellation("CGO-005", "gm-commercial", "buyer pulled tender")
    after = _pl.run(seed=3, weeks=12)
    assert "CGO-005" in after["cancelled"]


def test_reschedule_reroute_and_nearest(tmp_path, monkeypatch):
    import charterplanner.requests_store as st
    for attr, name in [("_ADD", "a"), ("_CANCEL", "c"), ("_RESCHED", "r"), ("_REROUTE", "x")]:
        monkeypatch.setattr(st, attr, tmp_path / (name + ".jsonl"))
    st.record_reschedule("CGO-010", 5, "logistics-head")
    st.record_reroute("CGO-010", "GPL", "logistics-head")
    r = _pl.run(seed=3, weeks=12)
    p = next(x for x in r["scenario"]["parcels"] if x["id"] == "CGO-010")
    assert p["required_by_week"] == 5 and p["port"] == "GPL"
    alt = _data.nearest_feasible_port(_data.build_scenario(seed=3, weeks=12), "PPT", 70000)
    assert alt is not None and alt.id != "HDA"


def test_feeds_roundtrip(tmp_path):
    from charterplanner import feeds as fd
    fd.generate_sample_feeds(seed=3, weeks=12, feeds_dir=str(tmp_path))
    sc = fd.build_scenario_from_feeds(str(tmp_path))
    assert len(sc.parcels) == 24 and sc.weeks == 12
    assert _opt.verify(sc, _opt.optimize(sc, time_limit=10.0)).ok
