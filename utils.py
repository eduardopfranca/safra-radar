"""
Pure utility functions for Safra Radar.
No I/O, no side effects. Computation that multiple layers can share lives here.
"""


def calculate_delta_abs(
    current: float | int | None,
    previous: float | int | None,
) -> float | None:
    """
    Returns the absolute difference between current and previous.

    Returns None if either input is None.
    """
    if current is None or previous is None:
        return None
    return float(current) - float(previous)


def calculate_delta_pct(
    current: float | int | None,
    previous: float | int | None,
) -> float | None:
    """
    Returns the percentage change from previous to current.

    Formula: ((current - previous) / previous) * 100
    Returns None if either input is None or if previous == 0.
    """
    if current is None or previous is None:
        return None
    if previous == 0:
        return None
    return ((float(current) - float(previous)) / float(previous)) * 100
