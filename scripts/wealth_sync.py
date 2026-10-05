#!/data/data/com.termux/files/usr/bin/python3
"""
Wealth Sync — Reads ledger + metal_holdings, prices metals via MetalpriceAPI,
writes a fresh snapshot to wealth_tracking.
"""
import os
import sys
import json
import subprocess
import requests

sys.path.insert(0, os.path.expanduser("~/imperial_network/scripts"))
from metal_client import get_metal_prices
import os as _os
def _mysql_password():
    pwd = _os.environ.get("MYSQL_ROOT_PASSWORD", "")
    if pwd:
        return pwd
    try:
        with open(_os.path.expanduser("~/.my.cnf")) as f:
            for line in f:
                if line.startswith("password="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


DB = "imperial_nexus"
USD_ZAR_FALLBACK = 18.50

def db_query(sql):
    """Run SQL via mariadb client using ~/.my.cnf credentials."""
    cmd = ["mariadb", DB, "-N", "-B", "-e", sql]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[DB ERROR] {result.stderr.strip()}")
        return None
    return result.stdout.strip()

def db_exec(sql):
    return db_query(sql)

def get_usd_zar():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10)
        rate = r.json().get("rates", {}).get("ZAR")
        if rate:
            print(f"[FX] USD/ZAR = {rate}")
            return float(rate)
    except Exception as e:
        print(f"[FX ERROR] {e}")
    print(f"[FX] Fallback rate: {USD_ZAR_FALLBACK}")
    return USD_ZAR_FALLBACK

def get_holdings():
    out = db_query("SELECT metal, quantity FROM metal_holdings;")
    holdings = {}
    if not out:
        return holdings
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[1]:
            holdings[parts[0]] = float(parts[1])
    return holdings

def calc_metal_value(prices, holdings, usd_zar):
    total = 0.0
    breakdown = {}
    rates = prices.get("rates", {})
    for metal, qty in holdings.items():
        rate = rates.get(metal)
        if not rate or qty == 0:
            continue
        usd_per_unit = 1.0 / rate
        zar_per_unit = usd_per_unit * usd_zar
        val = qty * zar_per_unit
        total += val
        breakdown[metal] = {
            "quantity": qty,
            "usd_per_unit": round(usd_per_unit, 2),
            "zar_per_unit": round(zar_per_unit, 2),
            "zar_value": round(val, 2),
        }
        print(f"[METAL] {metal}: {qty} @ R{zar_per_unit:,.2f} = R{val:,.2f}")
    return total, breakdown

def sync():
    print("=== WEALTH SYNC START ===")

    prices = get_metal_prices()
    if not prices or "rates" not in prices:
        print("[WARN] No metal prices available — using R0 for metals.")
        prices = {"rates": {}}

    usd_zar = get_usd_zar()
    holdings = get_holdings()

    metal_value, _ = calc_metal_value(prices, holdings, usd_zar) if holdings else (0.0, {})

    cash_out = db_query("SELECT COALESCE(SUM(amount),0) FROM ledger WHERE category='revenue';")
    cash = float(cash_out) if cash_out else 0.0
    print(f"[LEDGER] Cash revenue: R{cash:,.2f}")

    total_portfolio = cash + metal_value
    print(f"[TOTAL] Portfolio: R{total_portfolio:,.2f} (Metals: R{metal_value:,.2f})")

    sql = (f"INSERT INTO wealth_tracking "
           f"(portfolio_value, gain_value, true_valuation, last_updated) "
           f"VALUES ({total_portfolio}, {metal_value}, {total_portfolio}, NOW());")
    if db_exec(sql) is not None:
        print("[DB] Snapshot written to wealth_tracking")
    else:
        print("[DB ERROR] Could not write snapshot")

    print("=== WEALTH SYNC COMPLETE ===")

if __name__ == "__main__":
    sync()
