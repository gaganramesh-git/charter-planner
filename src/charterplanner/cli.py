"""Command line for Charter Planner (SIH26006)."""

from __future__ import annotations

import json
import pathlib

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(add_completion=False, help="Charter Planner — bulk-cargo vessel-chartering optimiser.")
console = Console()


@app.command()
def charter(
    seed: int = typer.Option(3, help="Scenario seed."),
    weeks: int = typer.Option(12, help="Planning horizon in weeks."),
    out: str = typer.Option("charter_schedule.json", help="Where to write the JSON report."),
    dashboard: str = typer.Option("charter_dashboard.html", help="Where to write the HTML dashboard."),
    from_feeds: bool = typer.Option(False, "--from-feeds",
        help="Plan from the CSV feeds in data/feeds instead of the generator."),
) -> None:
    """Optimise bulk-cargo vessel chartering on India's East Coast."""
    from . import data as _md
    from . import pipeline as mp
    from .dashboard import build_html

    report = mp.run(seed=seed, weeks=weeks, from_feeds=from_feeds)
    pathlib.Path(out).write_text(json.dumps(report, indent=2))
    pathlib.Path(dashboard).write_text(build_html(report))
    m = report["metrics"]
    console.print(f"\n[bold]{report['problem']}[/]  ([dim]{report['org']}[/])")
    console.print(
        f"[green]Freight cost:[/] optimised [bold]{_md.inr(m['ours_cost'])}[/] vs spot "
        f"[bold red]{_md.inr(m['spot_cost'])}[/]  → saved [bold green]{m['cost_saved_pct']}%[/] "
        f"({_md.inr(m['cost_saved'])})"
    )
    t = Table(title="Chartering plan vs reactive spot")
    for c in ("", "Optimised", "Reactive spot"):
        t.add_column(c, justify="right")
    t.add_row("Charters used", str(m["ours_voyages"]), str(m["spot_voyages"]))
    t.add_row("Parcels on time", f"{m['ours_served']}/{m['total_parcels']}", f"{m['spot_served']}/{m['total_parcels']}")
    t.add_row("Vessel utilisation", f"{m['utilisation_pct']}%", "—")
    t.add_row("Verified", "✓" if report["verification"]["ok"] else "✗", "—")
    console.print(t)
    console.print(f"\n[green]Wrote[/] {out} and [green]{dashboard}[/] (open it directly).")


@app.command(name="charter-serve")
def charter_serve(host: str = typer.Option("127.0.0.1"), port: int = typer.Option(8000)) -> None:
    """Live server — roles, audit, raise a cargo requirement, cancel/reschedule, port disruption."""
    from .service import serve as _serve
    console.print(f"[green]Live Charter Planner:[/] http://{host}:{port}  (Ctrl-C to stop)")
    _serve(host=host, port=port)


@app.command(name="charter-feeds")
def charter_feeds(seed: int = typer.Option(3), weeks: int = typer.Option(12),
                  out: str = typer.Option("data/feeds")) -> None:
    """Generate the CSV feeds (ports, vessels, origins, cargo demand, freight rates)."""
    from . import feeds as mf
    info = mf.generate_sample_feeds(seed=seed, weeks=weeks, feeds_dir=out)
    console.print(f"[green]Wrote feeds to {out}/[/] — {info['parcels']} cargo parcels, "
                  f"{info['rate_rows']} freight-rate rows "
                  f"(calibrated to Baltic {info['baltic']['date']}: BDI {info['baltic']['BDI']}).")
    console.print("Run: [bold]charter --from-feeds[/]")


@app.command(name="charter-eval")
def charter_eval(seeds: int = typer.Option(20), weeks: int = typer.Option(12)) -> None:
    """Evidence across many scenarios: optimised chartering vs reactive spot."""
    from . import pipeline as mp
    r = mp.run_eval(seeds=seeds, weeks=weeks)
    t = Table(title=f"Chartering evidence across {r['seeds']} scenarios")
    for c in ("Metric", "Mean ± SD"):
        t.add_column(c)
    t.add_row("Freight cost saved %", f"{r['cost_saved_pct'][0]} ± {r['cost_saved_pct'][1]}")
    t.add_row("Charters saved", f"{r['voyages_saved'][0]} ± {r['voyages_saved'][1]}")
    t.add_row("Cargo on time %", f"{r['on_time_pct'][0]} ± {r['on_time_pct'][1]}")
    t.add_row("Vessel utilisation %", f"{r['utilisation_pct'][0]} ± {r['utilisation_pct'][1]}")
    t.add_row("Parcels / voyage", f"{r['parcels_per_voyage'][0]} ± {r['parcels_per_voyage'][1]}")
    t.add_row("Solve time (s)", f"{r['solve_seconds'][0]} ± {r['solve_seconds'][1]}")
    console.print(t)
    console.print(f"[green]All plans independently verified:[/] {r['all_verified']}")


def main() -> None:
    app()


if __name__ == "__main__":
    app()
