import os
import re
import time
from datetime import date, timedelta

import requests

NSW_BASE = "http://www.valuergeneral.nsw.gov.au/__psi"
ABS_LATEST_RELEASE_URL = (
    "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/"
    "total-value-dwellings/latest-release"
)
USER_AGENT = "PRT661-Sydn2-Theme2-DataAcquisition/1.0 (student project; contact via GitHub repo)"


def _get(url, **kwargs):
    return requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60, **kwargs)


def download_nsw_yearly(years, output_dir="raw_data/nsw/yearly"):
    """Download one zip per year, e.g. 2016.zip, for historic full-year archives.

    years: iterable of ints, e.g. range(2014, 2026)
    """
    os.makedirs(output_dir, exist_ok=True)
    downloaded = []
    for year in years:
        url = f"{NSW_BASE}/yearly/{year}.zip"
        dest = os.path.join(output_dir, f"{year}.zip")
        if os.path.exists(dest):
            print(f"  [skip] {year}.zip already downloaded")
            downloaded.append(dest)
            continue
        try:
            resp = _get(url, stream=True)
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
            print(f"  [ok] {year}.zip")
            downloaded.append(dest)
        except requests.RequestException as e:
            print(f"  [fail] {year}.zip — {e}")
        time.sleep(1)  # be polite to a government server
    return downloaded


def _mondays_between(start: date, end: date):
    d = start - timedelta(days=start.weekday())  # snap back to Monday
    while d <= end:
        yield d
        d += timedelta(days=7)


def download_nsw_weekly(start_date: date, end_date: date, output_dir="raw_data/nsw/weekly"):
    """Download one zip per week (each dated on the Monday it was published)."""
    os.makedirs(output_dir, exist_ok=True)
    downloaded = []
    for monday in _mondays_between(start_date, end_date):
        stamp = monday.strftime("%Y%m%d")
        url = f"{NSW_BASE}/weekly/{stamp}.zip"
        dest = os.path.join(output_dir, f"{stamp}.zip")
        if os.path.exists(dest):
            print(f"  [skip] {stamp}.zip already downloaded")
            downloaded.append(dest)
            continue
        try:
            resp = _get(url, stream=True)
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
            print(f"  [ok] {stamp}.zip")
            downloaded.append(dest)
        except requests.RequestException as e:
            # Some weeks legitimately don't exist (public holidays, etc.) — log and move on.
            print(f"  [skip/fail] {stamp}.zip — {e}")
        time.sleep(1)
    return downloaded


def download_abs_total_value_of_dwellings(output_dir="raw_data/abs"):
    """Fetch the ABS Total Value of Dwellings 'latest-release' page, find the
    current Table 1 (Total value of dwellings, all series) spreadsheet link,
    and download it. The link changes every quarter, so we parse the page
    instead of hardcoding a URL.
    """
    os.makedirs(output_dir, exist_ok=True)
    resp = _get(ABS_LATEST_RELEASE_URL)
    resp.raise_for_status()
    html = resp.text

    # ABS data-download links are absolute or root-relative .xlsx links; the
    # link text usually contains "Table 1" for the total-value series.
    candidates = re.findall(r'href="([^"]+\.xlsx)"', html, flags=re.IGNORECASE)
    if not candidates:
        raise RuntimeError(
            "No .xlsx links found on the ABS latest-release page — "
            "the page structure may have changed; inspect it manually."
        )

    table1_url = candidates[0]
    if table1_url.startswith("/"):
        table1_url = "https://www.abs.gov.au" + table1_url

    dest = os.path.join(output_dir, "ABS_total_value_of_dwellings_latest.xlsx")
    file_resp = _get(table1_url, stream=True)
    file_resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in file_resp.iter_content(chunk_size=1 << 16):
            f.write(chunk)
    print(f"  [ok] ABS Total Value of Dwellings -> {dest}")
    return dest


if __name__ == "__main__":
    print("Downloading NSW yearly archives (2014-2025)...")
    download_nsw_yearly(range(2014, 2026))

    print("Downloading NSW weekly archives (2026 to date)...")
    download_nsw_weekly(date(2026, 1, 1), date.today())

    print("Downloading ABS Total Value of Dwellings...")
    download_abs_total_value_of_dwellings()
