"""Canonical tick-frame schema — single source of truth for all writers/readers.

Representation (audit round-4):
    pandas DataFrame, index = UTC DatetimeIndex (ns),
    columns = [bid, ask, (optional _seq)]; storage = (utc_ms, seq, bid, ask).

Refreshes preserve quote occurrence order. Conflicting overlaps fail and
require explicit recovery from complete source exports. Recovery replaces
stored order after checking that no stored quote occurrence is lost.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

TICK_COLUMNS = ["bid", "ask"]
SEQ_COL = "_seq"
STORE_MANIFEST = "store_manifest.json"


def with_seq(df: pd.DataFrame, start: int = 0) -> pd.DataFrame:
    """Assign monotone sequence numbers to a tick frame (arrival order)."""
    out = df.copy()
    out[SEQ_COL] = np.arange(start, start + len(out), dtype="int64")
    return out


def tick_dedup_consecutive(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse only CONSECUTIVE identical records (A→A); keep A→B→A revisits."""
    name = df.index.name
    reset = df.reset_index()
    idx_col = reset.columns[0]
    key = ["bid", "ask"]
    dup_mask = (reset[key] == reset[key].shift(1)).all(axis=1) & (reset[idx_col] == reset[idx_col].shift(1))
    n_before = len(reset)
    reset = reset[~dup_mask]
    if len(reset) < n_before:
        print(f"    [tick-dedup] {n_before - len(reset):,} consecutive duplicate records collapsed")
    return reset.set_index(idx_col).rename_axis(name)


def tick_dedup_exact_global(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate (ts,bid,ask) rows ANYWHERE in the frame (used when
    merging overlapping exports of the SAME source, where repeats are
    re-transmissions, not market revisits)."""
    name = df.index.name
    reset = df.reset_index()
    idx_col = reset.columns[0]
    n_before = len(reset)
    reset = reset.drop_duplicates(subset=[idx_col, "bid", "ask"], keep="first")
    if len(reset) < n_before:
        print(f"    [tick-dedup] {n_before - len(reset):,} exact duplicate records dropped")
    return reset.set_index(idx_col).rename_axis(name)


def merge_refresh(existing: pd.DataFrame, incoming: pd.DataFrame,
                  watermark: int | None = None) -> tuple[pd.DataFrame, int]:
    """Append a source export only when its overlap agrees in arrival order.

    Repeated quotes are matched as a sequence, preserving A→B→A. Conflicting
    or historical inserts require a complete export and explicit recovery.
    """
    existing = existing.sort_index(kind="mergesort")
    incoming = incoming.sort_index(kind="mergesort")
    current = int(existing[SEQ_COL].max()) if len(existing) else -1
    watermark = max(current, watermark if watermark is not None else -1)
    if len(existing) and len(incoming):
        if incoming.index[0] < existing.index[0]:
            raise ValueError("refresh starts before stored history; use recover_from_exports")
        overlap = existing.loc[incoming.index[0]:incoming.index[-1]]
        repeated = incoming.loc[:existing.index[-1]]
        n = len(overlap)
        same = (len(repeated) >= n and
                overlap.index.equals(repeated.index[:n]) and
                np.array_equal(overlap[TICK_COLUMNS].to_numpy(),
                               repeated[TICK_COLUMNS].iloc[:n].to_numpy()))
        if not same or (len(repeated) > n and incoming.index[len(incoming) - 1] < existing.index[-1]):
            raise ValueError("refresh overlap disagrees with source order; use recover_from_exports")
        incoming = incoming.iloc[n:]
    incoming = with_seq(incoming, watermark + 1)
    out = pd.concat([existing, incoming])
    return out, watermark + len(incoming)


def to_storage(df: pd.DataFrame) -> pd.DataFrame:
    """Column-store layout: utc_ms (int64 ms), seq, bid, ask — no index."""
    if isinstance(df.index, pd.DatetimeIndex):
        ms = df.index.asi8 // 1_000_000
    else:
        ms = df["utc_ms"]
    seq = df[SEQ_COL].to_numpy() if SEQ_COL in df.columns else np.arange(len(df), dtype="int64")
    out = pd.DataFrame({"utc_ms": pd.Series(ms).astype("int64").to_numpy(),
                        "seq": np.asarray(seq).astype("int64"),
                        "bid": df["bid"].to_numpy(),
                        "ask": df["ask"].to_numpy()})
    return out.reset_index(drop=True)


def from_storage(df: pd.DataFrame) -> pd.DataFrame:
    """Storage layout -> canonical tick frame (UTC DatetimeIndex + _seq)."""
    if "utc_ms" in df.columns:
        idx = pd.to_datetime(pd.to_numeric(df["utc_ms"], errors="coerce"),
                             unit="ms", utc=True)
        out = pd.DataFrame({"bid": df["bid"].to_numpy(), "ask": df["ask"].to_numpy()},
                           index=idx)
        if "seq" in df.columns:
            out[SEQ_COL] = df["seq"].to_numpy()
    elif isinstance(df.index, pd.DatetimeIndex):
        out = df[TICK_COLUMNS].copy()
        if SEQ_COL in df.columns:
            out[SEQ_COL] = df[SEQ_COL]
    else:
        raise ValueError(f"cannot interpret tick frame: columns={df.columns.tolist()}")
    out.index.name = None
    return out


def write_shard(df: pd.DataFrame, path: Path) -> None:
    """Tick frame -> canonical column-store parquet shard (with seq)."""
    pq.write_table(pa.Table.from_pandas(to_storage(df)), path)


def read_shard(path: Path) -> pd.DataFrame:
    """Canonical shard -> tick frame. Legacy layouts (no seq) get arrival-order
    seq within the shard + a chronology flag."""
    df = from_storage(pq.read_table(path).to_pandas())
    if SEQ_COL not in df.columns:
        df = with_seq(df)   # legacy: intra-shard order = the only order we have
    return df


def read_mt5_csv_frame(path) -> pd.DataFrame:
    """MT5 export CSV (utc_ms,bid,ask) -> canonical tick frame.

    Arrival order = row order in the export file (chronological source order).
    Consecutive duplicates collapse (repeated feed lines); non-consecutive
    exact repeats PRESERVED (possible quote revisits)."""
    import pyarrow.csv as pacsv
    t = pacsv.read_csv(
        str(path),
        read_options=pacsv.ReadOptions(skip_rows=1, autogenerate_column_names=True),
        convert_options=pacsv.ConvertOptions(
            column_types={"f0": pa.int64(), "f1": pa.float64(), "f2": pa.float64()}))
    t = t.rename_columns(["utc_ms", "bid", "ask"])
    df = t.to_pandas()
    idx = pd.to_datetime(df["utc_ms"], unit="ms", utc=True)
    out = pd.DataFrame({"bid": df["bid"].to_numpy(), "ask": df["ask"].to_numpy()}, index=idx)
    out = with_seq(tick_dedup_consecutive(out.sort_index(kind="mergesort")), start=0)
    return out


def recover_from_exports(export_dir: Path, shard_root: Path, pairs=None,
                         allow_loss: bool = False) -> dict:
    """Rebuild shards' chronology from the original export CSVs (round-4 fix).

    For each pair-month file present in the export dir, re-read with true
    arrival order and replace the old shard after checking that every stored
    quote occurrence is present. Sequence numbers are rebuilt from file order.

    allow_loss=True: accept replacement when the fresh export lacks stored
    occurrences, recording the loss explicitly in the store manifest
    (per-shard `lost_occurrences` count + timestamps). Never silent — the
    default refuses; use only when the export source is authoritative and
    the missing ticks are documented (server-side re-download variance).
    """
    import re
    fname_re = re.compile(r"^(?P<pair>[A-Z]{6})_ticks_(?P<yyyymm>\d{6})\.csv$")
    out = {}
    for csv in sorted(export_dir.glob("*_ticks_*.csv")):
        m = fname_re.match(csv.name)
        if not m:
            continue
        pair, yyyymm = m.group("pair"), m.group("yyyymm")
        if pairs and pair not in pairs:
            continue
        shard = shard_root / pair / f"{yyyymm}.parquet"
        fresh = read_mt5_csv_frame(csv)
        if fresh.empty:
            raise ValueError(f"empty recovery export: {csv}")
        loss_record = None
        if shard.exists():
            existing = read_shard(shard)
            # Require every stored quote occurrence, even when its order was
            # corrupted. A partial export must never erase stored history.
            keys = lambda df: pd.DataFrame({"ts": df.index.asi8,
                                            "bid": df.bid.to_numpy(), "ask": df.ask.to_numpy()})
            old_counts = keys(existing).value_counts()
            new_counts = keys(fresh).value_counts().reindex(old_counts.index, fill_value=0)
            missing_mask = new_counts < old_counts
            if missing_mask.any():
                n_missing = int((old_counts[missing_mask] - new_counts[missing_mask]).sum())
                if not allow_loss:
                    raise ValueError(f"recovery export lacks stored quote occurrences: {csv} "
                                     f"({n_missing} occurrences)")
                lost_keys = old_counts[missing_mask].index
                lost_ts = sorted(set(pd.to_datetime(lost_keys.get_level_values("ts"), utc=True)
                                     .strftime("%Y-%m-%dT%H:%M:%S")))
                loss_record = {"lost_occurrences": n_missing, "distinct_lost_quotes": int(missing_mask.sum()),
                               "timestamps_sample": lost_ts[:5]}
        shard.parent.mkdir(parents=True, exist_ok=True)
        write_shard(fresh, shard)
        entry = {"rebuilt_rows": len(fresh), "chronology": "source-arrival"}
        if loss_record:
            entry.update(loss_record)
        out[f"{pair}/{yyyymm}"] = entry
        mp = shard_root / STORE_MANIFEST
        manifest = json.loads(mp.read_text()) if mp.exists() else {}
        manifest.setdefault("shards", {})[f"{pair}/{yyyymm}"] = entry
        # Old bindings are retained: consumers reject them until a fresh run.
        mp.write_text(json.dumps(manifest, indent=2))
    return out


def normalize_store(root: Path) -> dict:
    """One-time migration + chronology bookkeeping.

    Shards without seq get arrival-order seq assigned (intra-shard order);
    the store manifest records that migrated shards are
    'recovered-unordered' for intra-ms chronology unless re-exported.
    """
    manifest_p = Path(root) / STORE_MANIFEST
    manifest = json.loads(manifest_p.read_text()) if manifest_p.exists() else {
        "chronology": "source-arrival", "shards": {}}
    n = 0
    for pdir in sorted(Path(root).glob("*")):
        if not pdir.is_dir():
            continue
        for shard in sorted(pdir.glob("*.parquet")):
            raw = pq.read_table(shard).to_pandas()
            df = from_storage(raw)
            if SEQ_COL not in df.columns:
                df = with_seq(df)
                key = f"{pdir.name}/{shard.stem}"
                if key not in manifest["shards"]:
                    manifest["shards"][key] = {"chronology": "recovered-unordered"}
            write_shard(df, shard)
            n += 1
    manifest["shards_normalized"] = n
    manifest_p.write_text(json.dumps(manifest, indent=2))
    return manifest