# MT5 Tick Export — Runbook (FX-LDN-001 data path)

**Purpose:** move real MT5 ticks (MetaQuotes-Demo or any broker) into the
`fxedge` research store, then run DATA gates + FX-LDN-001 on them.

---

## Step 1 — compile the export script (one-time, ~1 minute)

1. Open **MT5 → MetaEditor** (F4).
2. Copy `fxedge/mt5/ExportTicksFromMT5.mq5` (this repo) into
   `MQL5\Scripts\` of the terminal data folder:
   `~/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Scripts/`
3. Compile (F7). Fix nothing else; the script is self-contained.

## Step 2 — run the export in the terminal (one-time per refresh)

1. In MT5: **Navigator → Scripts → ExportTicksFromMT5** → drag onto any chart.
2. Defaults request **24 months** × 6 majors, chunked monthly
   (`COPY_TICKS_INFO` = Bid/Ask only). Press OK.
3. Wait for `FX_EDGE export complete.` in the **Experts** log.
4. Output lands in
   `Terminal\Common\Files\FX_EDGE\<PAIR>_ticks_<YYYYMM>.csv`
   (the wine path is
   `~/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/FX_EDGE/`).

Notes:
- MetaQuotes-Demo tick depth is whatever the server holds; months with no
  data simply won't produce files. The report records the actual coverage.
- Rough size: ~7,500 ticks/min/pair ≈ **1.5–4 GB compressed per major**.
  Export takes a few minutes per pair on demo.

## Step 3 — ingest to the canonical store (Python side)

```bash
cd fxedge
python -m fxedge.ingest_mt5          # auto-detects the wine Common/Files/FX_EDGE path
python -m fxedge.ingest_mt5 --pairs EURUSD,GBPUSD   # subset
```

Writes `data/fxedge/<PAIR>.parquet` (UTC-indexed bid/ask) — the layout the
existing `python -m fxedge` CLI reads.

## Step 4 — DATA gates + FX-LDN-001 on real data

```bash
python -m fxedge --data-root data/fxedge
```

Produces:
- `runs/quality_gates.json` (DATA-001/002/005 on the real feed)
- `runs/FX-LDN-001/report.json` + `sessions.parquet` (real base rates)

Everything downstream (DATA-003/004 session correctness, Gate L1 sanity
vs. synthetic) reads the same session table.

## Step 5 — record in the registry (before interpreting!)

Copy `fxedge/experiments/FX-LDN-001.registry-entry.md` into
`runs/FX-LDN-001/`, fill the result fields from `report.json` **before**
looking at any trading-oriented view of the data (spec §8 anti-storytelling).
The entry template pre-registers: no entry rule, no stops, no targets, no
ICT concepts, no optimization — it can only be a base-rate record.

---

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `no *_ticks_*.csv` during ingest | Export not run/finished in terminal | Re-run Step 2; check Experts log |
| Month files missing for a pair | Broker has no server history that month | Expected on demo; record coverage in registry entry |
| `negative spreads` in DATA-002 | Crossed quotes from a demo feed blip | Cleaning rules frozen per §6, never silent |
| Export script "not in Market Watch" | Pair not subscribed | Open the pair's chart once (adds to Market Watch) |