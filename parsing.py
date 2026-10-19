"""Parse NSW Valuer General bulk property-sales archives (current 2001+ format).

The archives are nested: a yearly zip holds weekly zips (or weekly folders),
each holding one semicolon-delimited ``.DAT`` file per valuation district.
Only ``B`` records (one per sale) are needed; ``A`` is a file header, ``C`` the
legal description, ``D`` purchaser/vendor type flags, ``Z`` a trailer.

The parser streams archives in memory, so nothing is unpacked to disk and a
re-run is deterministic.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Iterator

import pandas as pd

# Field positions of a 'B' record (NSW VG "Current Property Sales Data File Format 2001 to Current")
B_FIELDS = {
    1: "district_code", 2: "property_id", 3: "sale_counter", 4: "download_datetime",
    5: "property_name", 6: "unit_number", 7: "house_number", 8: "street_name",
    9: "suburb", 10: "postcode", 11: "area", 12: "area_type", 13: "contract_date",
    14: "settlement_date", 15: "purchase_price", 16: "zoning", 17: "nature_of_property",
    18: "primary_purpose", 19: "strata_lot_number", 20: "component_code", 21: "sale_code",
    22: "interest_of_sale", 23: "dealing_number",
}


def _iter_dat_bytes(zf: zipfile.ZipFile, label: str) -> Iterator[tuple[str, bytes]]:
    for info in zf.infolist():
        name = info.filename
        if name.endswith("/"):
            continue
        low = name.lower()
        if low.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(zf.read(info))) as inner:
                yield from _iter_dat_bytes(inner, f"{label}/{name}")
        elif low.endswith(".dat"):
            yield f"{label}/{name}", zf.read(info)


def iter_b_records(archive: Path) -> Iterator[list[str]]:
    """Yield the raw field list of every B record inside one (possibly nested) archive."""
    with zipfile.ZipFile(archive) as zf:
        for src, payload in _iter_dat_bytes(zf, archive.name):
            for line in payload.decode("latin-1").splitlines():
                if line.startswith("B;"):
                    parts = line.split(";")
                    if len(parts) >= 24:
                        yield parts[:24] + [src]


def parse_archive(archive: Path, source_year: int) -> pd.DataFrame:
    rows = list(iter_b_records(archive))
    cols = ["record_type"] + [B_FIELDS[i] for i in range(1, 24)] + ["source_file"]
    df = pd.DataFrame(rows, columns=cols).drop(columns="record_type")
    df["source_year_archive"] = source_year
    return df


def list_archives(raw_dir: Path) -> list[tuple[Path, int]]:
    """Yearly archives plus any loose weekly zips for the current year."""
    out = []
    for p in sorted(raw_dir.glob("*.zip")):
        out.append((p, int(p.stem[:4])))
    return out


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ("property_id", "sale_counter", "purchase_price", "postcode"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["area"] = pd.to_numeric(df["area"], errors="coerce")
    for c in ("contract_date", "settlement_date"):
        df[c] = pd.to_datetime(df[c], format="%Y%m%d", errors="coerce")
    df["download_datetime"] = pd.to_datetime(df["download_datetime"], format="%Y%m%d %H:%M", errors="coerce")
    df["suburb"] = df["suburb"].str.strip().str.upper()
    return df


def parse_all(raw_dir: Path) -> pd.DataFrame:
    frames = []
    for archive, year in list_archives(raw_dir):
        part = parse_archive(archive, year)
        print(f"  parsed {archive.name:>10}: {len(part):>9,} B-records")
        frames.append(part)
    return coerce_types(pd.concat(frames, ignore_index=True))
