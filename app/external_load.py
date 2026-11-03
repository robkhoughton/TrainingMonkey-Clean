"""Running external load: Total Load Miles = distance + elevation gain / RUNNING_ELEVATION_FACTOR.

Single source for the running vert conversion (Training_Metrics_Reference_Guide.md § Elevation
Load Miles). Activity sync, planned-load display, race readiness and the long-run limits all
convert through here, so the long-run ceiling and the ACWR load can never use different factors.
"""

RUNNING_ELEVATION_FACTOR = 750.0  # feet of climbing counted as one mile of running load


def running_load_miles(distance_miles: float, elevation_gain_feet: float) -> float:
    """Total Load Miles for a running session."""
    return distance_miles + elevation_gain_feet / RUNNING_ELEVATION_FACTOR
