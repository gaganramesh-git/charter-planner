# Charter Planner

**AI freight-forecasting & optimised bulk-cargo vessel chartering for India's East Coast.**
Smart India Hackathon 2026 · Problem Statement **SIH26006** · Ministry of Steel.

Charter Planner is the decision layer bulk-cargo chartering is missing: instead of
buying spot one shipload at a time, it plans every cargo together — choosing the
**vessel class** and **departure week** for each parcel to meet delivery deadlines at
the lowest freight cost, within each port's physical limits.

## What it does

- **Optimises** with Google OR-Tools **CP-SAT**: assigns cargo parcels to voyages,
  minimising freight cost + idle capacity, honouring **port draft**, **ship capacity**
  and **delivery deadlines** as hard constraints, and **consolidating** parcels onto
  fewer, fuller ships.
- **Times the market**: recommends the cheapest week to charter each vessel class from
  a freight-rate outlook calibrated to the **Baltic Exchange** sub-indices
  (BCI / BPI / BSI / BHSI).
- **Proves every plan**: an independent checker re-validates the schedule, and it is
  benchmarked against today's reactive **spot** procurement.
- **Operable**: role-based access with a full audit trail; raise a cargo requirement,
  bulk-import by CSV, reschedule, cancel, or declare a port disruption and reroute —
  each re-plans live.

## Evidence (20 scenarios, every plan verified)

| Metric | Result vs reactive spot |
|---|---|
| Freight cost saved | ~6.6% |
| Charters used | ~2 fewer per plan |
| Cargo on time | 100% |
| Vessel utilisation | ~88% |
| Solve time | < 1 s |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .

charter                 # solve, write charter_schedule.json + charter_dashboard.html
charter --from-feeds    # plan from the CSV feeds in data/feeds
charter-feeds           # (re)generate the sample CSV feeds
charter-eval            # evidence across many scenarios
charter-serve           # live dashboard at http://127.0.0.1:8000
```

## Data & honesty

Freight is quoted in USD (Baltic); amounts are shown in INR at a stated ₹88/USD.
The forward freight series is **modelled, calibrated** to real Baltic index levels —
not a live feed — and cargo demand is synthetic or CSV-fed. Live BDMS/COA/market-feed
integration is the next step; the CSV adapter layer already exists for it. These
caveats are stated in the product rather than hidden.

## Layout

```
src/charterplanner/
  model.py        domain types (ports, vessels, origins, parcels, voyages)
  data.py         real-ish East-Coast ports/vessels, scenario + freight-rate generator, INR
  optimizer.py    CP-SAT optimiser, reactive-spot baseline, independent checker
  pipeline.py     end-to-end run + report + multi-scenario evaluator
  feeds.py        CSV adapters (ports/vessels/origins/cargo/freight rates)
  requests_store.py  persisted operator edits (add / cancel / reschedule / reroute)
  audit.py        role hierarchy + hierarchy-filtered audit log
  dashboard.py    self-contained HTML dashboard
  entry.py        cargo-requirement entry screen
  cli.py          charter / charter-serve / charter-eval / charter-feeds
tests/            property tests guarding the headline claims
data/feeds/       sample CSV feeds
```

## License

Apache-2.0.
