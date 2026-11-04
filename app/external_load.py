"""Running external load: Total Load Miles = distance + elevation gain / RUNNING_ELEVATION_FACTOR.

Single source for the running vert conversion (Training_Metrics_Reference_Guide.md § Elevation
Load Miles). Activity sync, planned-load display, race readiness, the long-run limits and the
autopsy's volume compliance all convert through here, so none of them can use a different factor
from the ACWR load.
"""

from typing import NamedTuple, Optional

RUNNING_ELEVATION_FACTOR = 750.0  # feet of climbing counted as one mile of running load


def running_load_miles(distance_miles: float, elevation_gain_feet: float) -> float:
    """Total Load Miles for a running session."""
    return distance_miles + elevation_gain_feet / RUNNING_ELEVATION_FACTOR


class VolumeCompliance(NamedTuple):
    """Prescribed vs actual volume for one day, in load miles with the distance/vert split."""
    target_distance_miles: float
    target_elevation_gain_feet: float
    target_load_miles: float
    actual_distance_miles: float
    actual_elevation_gain_feet: float
    actual_load_miles: float


def volume_compliance(target_distance_miles: float, target_elevation_gain_feet: float,
                      actual_distance_miles: float, actual_elevation_gain_feet: float,
                      actual_load_miles: float) -> VolumeCompliance:
    """Pair a prescription with the day's actual volume.

    actual_load_miles is the stored activities.total_load_miles sum (the ACWR load), not a
    recomputation, so the autopsy judges the same load the metrics count.
    """
    return VolumeCompliance(
        target_distance_miles=target_distance_miles,
        target_elevation_gain_feet=target_elevation_gain_feet,
        target_load_miles=running_load_miles(target_distance_miles, target_elevation_gain_feet),
        actual_distance_miles=actual_distance_miles,
        actual_elevation_gain_feet=actual_elevation_gain_feet,
        actual_load_miles=actual_load_miles,
    )


def _pct_change(actual: float, target: float) -> Optional[float]:
    return None if target <= 0 else (actual - target) / target * 100


def _fmt_pct(pct: Optional[float]) -> str:
    return "no target" if pct is None else f"{pct:+.0f}%"


def format_volume_compliance(vc: VolumeCompliance) -> str:
    """The prescribed-vs-actual volume lines, every number computed here, none by the model."""
    factor = f"{RUNNING_ELEVATION_FACTOR:.0f}"
    return (
        f"Prescribed: {vc.target_distance_miles:.1f} mi + {vc.target_elevation_gain_feet:,.0f} ft "
        f"= {vc.target_load_miles:.1f} load miles\n"
        f"Actual: {vc.actual_distance_miles:.1f} mi + {vc.actual_elevation_gain_feet:,.0f} ft "
        f"= {vc.actual_load_miles:.1f} load miles\n"
        f"Load miles: {_fmt_pct(_pct_change(vc.actual_load_miles, vc.target_load_miles))} "
        f"(distance {_fmt_pct(_pct_change(vc.actual_distance_miles, vc.target_distance_miles))}, "
        f"vert {_fmt_pct(_pct_change(vc.actual_elevation_gain_feet, vc.target_elevation_gain_feet))})\n"
        f"(Load miles = distance + elevation gain / {factor}.)"
    )
