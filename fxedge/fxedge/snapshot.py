"""Store snapshot binding: one identity for the data store; all runs must
reference THE SAME snapshot, and evidence renderers must validate agreement.

Audit round-4 finding #4: the manifest fingerprint (sampled shard-head hashes)
and a different byte count appeared in different committed artifacts — produced
by separate fingerprinting moments and unchecked mixing. Fix:

- `snapshot_id`: stable hash of EVERY shard path + size + content-length-hash.
  Expensive mode: full sha256 of each shard (used once per rerun).
- Runs record (snapshot_id, per-pair byte counts) ONCE in the store manifest.
- Any later fingerprint must equal it; `reject_mismatch` enforces identity
  in evidence generation and precondition gates.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

STORE_MANIFEST = "store_manifest.json"


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_id(root: Path, full_hash: bool = True) -> dict:
    """Identity of the shard store: per-pair (n_shards, bytes, hash) + global id."""
    root = Path(root)
    pairs = {}
    ids = []
    for pdir in sorted(root.glob("*")):
        if not pdir.is_dir():
            continue
        shards = sorted(pdir.glob("*.parquet"))
        if not shards:
            continue
        byte_total = sum(s.stat().st_size for s in shards)
        if full_hash:
            hh = hashlib.sha256()
            for s in shards:
                hh.update(s.stem.encode())
                hh.update(_sha256_file(s).encode())
            pair_hash = hh.hexdigest()
        else:
            hh = hashlib.sha256()
            for s in shards:
                hh.update(s.stem.encode())
                hh.update(str(s.stat().st_size).encode())
            pair_hash = hh.hexdigest()
        pairs[pdir.name] = {"n_shards": len(shards), "bytes": byte_total, "hash": pair_hash}
        ids.append(f"{pdir.name}:{pair_hash}")
    gid = hashlib.sha256("|".join(ids).encode()).hexdigest()
    return {"snapshot_id": gid, "pairs": pairs}


def load_or_create(root: Path) -> dict:
    """The store manifest carries THE snapshot. Once written, it is immutable:
    a differing re-fingerprint raises instead of silently updating."""
    p = Path(root) / STORE_MANIFEST
    snap = snapshot_id(root)
    snap["chronology"] = json.loads(p.read_text()).get("chronology_status") if p.exists() else None
    if p.exists():
        old = json.load(open(p))
        if "snapshot_id" in old and old["snapshot_id"] != snap["snapshot_id"]:
            raise RuntimeError(
                "store snapshot changed vs manifest: data store was modified after runs bound to it. "
                f"old={old['snapshot_id'][:12]} new={snap['snapshot_id'][:12]} — rebind or revert.")
        # fill in snapshot for legacy manifests
        old.update(snap)
        p.write_text(json.dumps(old, indent=2))
        return old
    p.write_text(json.dumps(snap, indent=2))
    return snap


def reject_mismatch(run_snapshot: dict, store_manifest: dict, where: str) -> None:
    """Evidence-agreement check: a rendered artifact may only mix fields from
    artifacts bound to the SAME store snapshot and the same byte counts."""
    if run_snapshot.get("snapshot_id") != store_manifest.get("snapshot_id"):
        raise RuntimeError(f"{where}: snapshot_id mismatch — evidence is not from one data snapshot")
    for pair, rp in run_snapshot.get("pairs", {}).items():
        sp = store_manifest.get("pairs", {}).get(pair)
        if sp and rp["bytes"] != sp["bytes"]:
            raise RuntimeError(f"{where}: byte count mismatch for {pair} "
                               f"({rp['bytes']} vs {sp['bytes']}) — artifacts disagree")


# Back-compat: fingerprint_store now aliases the snapshot (with full hash).
def fingerprint_store(root: Path) -> dict:
    return snapshot_id(root)