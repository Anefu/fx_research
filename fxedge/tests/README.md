Run the regression suite from the repository root:

```sh
python -m pip install numpy pandas pyarrow
PYTHONPATH=fxedge python -m unittest discover -s fxedge/tests -v
```

The tests create small CSV and Parquet stores. They do not need the historical MT5 dataset.

Refreshes accept matching source sequences and append new quotes. Conflicting overlaps fail and retain the CSV. Use `recover_from_exports` with complete source exports to rebuild old chronology. Recovery checks quote occurrence counts before replacing a shard.

Both `real_run.run` and `run_ldn_001_v2` accept `start_month` and `end_month` as YYYYMM integers. Set them explicitly for a registered study. Otherwise they check every calendar month between the earliest and latest shards across the store. This default detects gaps inside that span; it cannot infer missing history outside it.

Regenerate DATA gates and sessions against the same store and month span, then rerun `ldn_002_004_v2`. The inference gate hashes live shards and the session table and requires matching artifact bindings. If an existing `store_manifest.json` contains an old snapshot binding, explicitly rebind that manifest with the current full snapshot after reviewing the changed store; preserve its chronology records. Unresolved chronology remains a blocker.

Previously committed registry results are historical. This fix changes methodology hashes and does not validate or refresh those results. The full dataset must be rerun before using them as current evidence.
