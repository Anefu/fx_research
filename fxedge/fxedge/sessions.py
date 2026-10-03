"""Session clock engine: DST-aware London session windows per calendar day.

All raw data is UTC (fx-edge-experiment-registry.md section 0). Session
windows are expressed in Europe/London local time and converted to UTC
per-day, so a window shifts by one hour across DST boundary days.

Windows are half-open UTC intervals [start, end). Registry end stamps
("06:59", "10:00") are inclusive minutes, so the UTC end is +1 minute.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc


@dataclass(frozen=True)
class SessionWindow:
    """A contiguous UTC half-open interval [start, end) for one London-local day."""
    start_utc: datetime   # aware, UTC
    end_utc: datetime     # aware, UTC, exclusive
    london_date: str      # YYYY-MM-DD London-local calendar day
    dst_summer: bool      # True if London was on BST during the window

    @property
    def minutes(self) -> int:
        return int((self.end_utc - self.start_utc).total_seconds() // 60)


def _hhmm(s: str) -> tuple:
    h, m = s.split(":")
    return int(h), int(m)


def _local(day: date, hhmm: str, ltz: ZoneInfo) -> datetime:
    h, m = _hhmm(hhmm)
    return datetime(day.year, day.month, day.day, h, m, tzinfo=ltz)


def dst_on(dt_aware: datetime, ltz: ZoneInfo) -> bool:
    """True if the London-local timestamp is inside BST (summer time)."""
    winter = datetime(2021, 1, 15, 0, 0, tzinfo=ltz).utcoffset()
    return dt_aware.astimezone(ltz).utcoffset() > winter


class SessionEngine:
    def __init__(self, frozen):
        self.f = frozen
        self.ltz = ZoneInfo(frozen.london_tz)

    def is_fx_day(self, d: date) -> bool:
        """Registry definition: the 00:00-06:59 London Asia window exists
        Monday..Friday only; Saturday/Sunday sessions are never formed,
        so weekend-contaminated weeks cannot enter the sample."""
        return d.weekday() < 5

    def asia_and_london(self, d: date):
        """(asia_window, london_window) for London-local day `d`, or None.

        Asia window:   [00:00, 07:00) London  == registry "00:00-06:59" inclusive.
        London window: [07:00, 10:01) London  == registry "07:00-10:00" inclusive.
        """
        if not self.is_fx_day(d):
            return None

        def win(hhmm_start: str, hhmm_end_incl: str) -> SessionWindow:
            start = _local(d, hhmm_start, self.ltz).astimezone(UTC)
            # inclusive minute stamp -> +1 minute, exclusive end
            h, m = _hhmm(hhmm_end_incl)
            t = h * 60 + (m + 1)
            end_local = datetime(d.year, d.month, d.day, 0, 0, tzinfo=self.ltz) + timedelta(minutes=t)
            end = end_local.astimezone(UTC)
            return SessionWindow(
                start_utc=start,
                end_utc=end,
                london_date=d.isoformat(),
                dst_summer=dst_on(start, self.ltz),
            )

        asia = win(self.f.asia_start, self.f.asia_end)
        ldn = win(self.f.london_window_start, self.f.london_window_end)
        return asia, ldn, (asia.dst_summer and ldn.dst_summer)

    def sessions_for_range(self, first_day: date, last_day: date) -> list:
        out = []
        d = first_day
        while d <= last_day:
            r = self.asia_and_london(d)
            if r is not None:
                out.append((r[0], r[1], r[2]))
            d += timedelta(days=1)
        return out