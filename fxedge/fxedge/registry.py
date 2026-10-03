"""FX-LDN registry: frozen Generation-1 parameters.

Every value here comes from fx-edge-experiment-registry.md section 0
(Global Frozen Definitions). Nothing in this file may be edited without
creating a new registry version.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class Frozen:
    # --- universe -------------------------------------------------------
    primary_universe: Tuple[str, ...] = (
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF",
    )
    secondary_universe: Tuple[str, ...] = (
        "EURGBP", "EURJPY", "GBPJPY", "AUDJPY",
    )

    # --- time conventions ------------------------------------------------
    raw_timezone: str = "UTC"
    london_tz: str = "Europe/London"      # DST-aware
    new_york_tz: str = "America/New_York"  # DST-aware
    daily_close_ny: str = "17:00 America/New_York"

    # --- session windows (London local time) ------------------------------
    asia_start: str = "00:00"
    asia_end: str = "06:59"               # inclusive last minute
    london_window_start: str = "07:00"
    london_window_end: str = "10:00"

    # --- compression --------------------------------------------------------
    compression_lookback: int = 60        # previous valid sessions
    compression_primary: float = 0.30     # Asia range <= 30th percentile of prev 60
    compression_plateau: Tuple[float, ...] = (0.20, 0.25, 0.30, 0.35, 0.40)

    # --- expansion events ---------------------------------------------------
    expansion_event_1: float = 1.0        # ER > 1.0
    expansion_event_2: float = 1.5        # ER > 1.5

    # --- trend -------------------------------------------------------------
    htf_trend_lookback_days: int = 20     # previous completed 20 trading sessions
    trend_lookback_plateau: Tuple[int, ...] = (5, 10, 20, 40, 60)

    # --- bars ---------------------------------------------------------------
    decision_bars: str = "5m"
    bar_grid: Tuple[str, ...] = ("1m", "5m", "15m")

    # --- forward-return horizons (minutes) ----------------------------------
    forward_horizons_min: Tuple[int, ...] = (15, 30, 60, 180)

    # --- OOS structure -------------------------------------------------------
    dev_frac: float = 0.60
    val_frac: float = 0.20
    holdout_frac: float = 0.20

    # --- research currency ----------------------------------------------------
    r_multiple_only: bool = True

    def london_window_bounds(self) -> Tuple[str, str]:
        """Asia end is inclusive; the London window starts the next minute."""
        h, m = self.asia_end.split(":")
        end_excl_min = int(h) * 60 + int(m) + 1
        return f"00:00", f"{end_excl_min // 60:02d}:{end_excl_min % 60:02d}"


# The single frozen instance. Import this everywhere.
FRZ = Frozen()

# Registry metadata for every output artifact.
REGISTRY_VERSION = "1.0"
REGISTRY_ID = "GEN-1"

# Sessions missing either window are invalid and excluded everywhere.
SESSION_INVALID_REASON = "missing-or-outside-window"


def validate_freeze() -> Dict[str, str]:
    """Sanity checks on the frozen parameters (registry-internal consistency)."""
    problems = {}
    if FRZ.asia_end >= FRZ.london_window_start:
        problems["windows"] = "Asia end must be before London window start"
    if FRZ.compression_primary > 1.0 or FRZ.compression_primary <= 0.0:
        problems["compression"] = "Primary compression threshold must be in (0, 1]"
    if len(FRZ.primary_universe) != 6:
        problems["universe"] = "Primary universe must have exactly 6 pairs"
    if abs(FRZ.dev_frac + FRZ.val_frac + FRZ.holdout_frac - 1.0) > 1e-9:
        problems["oos"] = "Dev/val/holdout fractions must sum to 1"
    return problems


if __name__ == "__main__":
    p = validate_freeze()
    print("freeze OK" if not p else f"freeze PROBLEMS: {p}")