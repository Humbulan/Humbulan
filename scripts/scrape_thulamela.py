#!/usr/bin/env python3
import os
"""
Thulamela Local Municipality tender scraper.
Only inserts tenders that are still open (closing_date >= today).
"""
import requests
import pymysql
import hashlib
import re
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

DB_CONFIG = {
    'user': 'root',
    'password': os.environ.get("MYSQL_ROOT_PASSWORD", ""),
    'unix_socket': '/data/data/com.termux/files/home/mysql_run/mysql.sock',
    'database': 'imperial_nexus',
}

TENDER_URLS = [
    "https://www.thulamela.gov.za/pages/tender1.php",
    "https://www.thulamela.gov.za/index.php/tenders",
]


def fetch_page(url):
    import time as _t
    for attempt in range(1, 4):
        try:
            r = requests.get(url, timeout=30,
                             headers={"User-Agent": "Mozilla/5.0 (compatible; Imperial-Nexus/1.0)"})
            r.raise_for_status()
            return r.text
        except Exception as e:
            if attempt < 3:
                print(f"[RETRY {attempt}/3] {url}: {str(e)[:80]}")
                _t.sleep(5 * attempt)
            else:
                print(f"[FETCH ERROR] {url}: {str(e)[:120]}")
    return None


def parse_tenders(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < 3:
                continue
            desc_cell = cells[0]
            link = desc_cell.find("a")
            if not link:
                continue
            description = desc_cell.get_text(" ", strip=True)
            href = link.get("href", "").strip()
            pdf_url = urljoin(base_url, href)
            uploaded = cells[1].get_text(strip=True)
            closing = cells[2].get_text(strip=True)
            if "description" in description.lower() and "closing" in closing.lower():
                continue
            if not description or not closing:
                continue
            rows.append({
                "title": description,
                "pdf_url": pdf_url,
                "uploaded": uploaded,
                "closing": closing,
            })
    return rows


def normalise_date(s):
    s = (s or "").strip()
    if not s:
        return ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0)
    for fmt in ("%d %B %Y", "%d %b %Y", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return ""


def classify_municipality(title):
    t = (title or "").lower()
    for name, kws in [
        ("Thulamela",       ["thulamela", "thohoyandou", "sibasa", "dzanani"]),
        ("Makhado",         ["makhado", "louis trichardt"]),
        ("Musina",          ["musina", "messina"]),
        ("Collins Chabane", ["collins chabane", "mutale"]),
        ("Vhembe",          ["vhembe"]),
    ]:
        if any(k in t for k in kws):
            return name
    return "Thulamela"


def make_key(title, pdf_url, closing):
    """Human-readable key derived from the tender title."""
    import re as _re
    s = _re.sub(r'[^A-Za-z0-9 ]', ' ', title or '')
    s = _re.sub(r'\s+', '-', s.strip().upper())[:45].strip('-')
    ymd = (closing or "").replace('-', '')[:8]
    return f"THUL-{s}-{ymd}"


def upsert(rows):
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    written = 0
    skipped = 0
    expired = 0
    today = datetime.now().date()

    for r in rows:
        closing = normalise_date(r["closing"])
        if not closing:
            skipped += 1
            continue
        # Only keep still-open tenders
        try:
            cdate = datetime.strptime(closing, "%Y-%m-%d").date()
        except Exception:
            skipped += 1
            continue
        if cdate < today:
            expired += 1
            continue

        key = make_key(r["title"], r["pdf_url"], closing)
        muni = classify_municipality(r["title"])

        try:
            cur.execute("""
                INSERT INTO tender_monitor
                  (tender_number, title, department, province, municipality,
                   closing_date, status, source_url, scraped_at, is_demo)
                VALUES (%s, %s, 'Thulamela Local Municipality', 'Limpopo', %s,
                        %s, 'active', %s, NOW(), 0)
                ON DUPLICATE KEY UPDATE
                  title=VALUES(title),
                  municipality=VALUES(municipality),
                  closing_date=VALUES(closing_date),
                  status='active',
                  source_url=VALUES(source_url),
                  scraped_at=NOW()
            """, (key, r["title"][:500], muni, closing, r["pdf_url"][:200]))
            written += 1
        except Exception as e:
            print(f"[DB SKIP] {r['title'][:40]}: {e}")
            skipped += 1

    conn.commit()
    conn.close()
    return {"parsed": len(rows), "written": written,
            "expired_skipped": expired, "other_skipped": skipped}


def main():
    print(f"[{datetime.now().isoformat()}] Scraping Thulamela")
    all_rows = []
    for url in TENDER_URLS:
        html = fetch_page(url)
        if not html:
            continue
        rows = parse_tenders(html, url)
        print(f"  {url}: {len(rows)} rows")
        all_rows.extend(rows)

    seen = set()
    unique = []
    for r in all_rows:
        k = (r["title"], r["pdf_url"])
        if k in seen:
            continue
        seen.add(k)
        unique.append(r)

    print(f"  unique: {len(unique)}")
    print(f"  {upsert(unique)}")


if __name__ == "__main__":
    main()
