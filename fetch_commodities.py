#!/usr/bin/env python3
"""Fetch SADC commodity prices from free sources."""
import json, re, urllib.request, subprocess
from pathlib import Path

PUSHGATEWAY = "http://127.0.0.1:9092"
JOB = "sadc_commodities"
CACHE = Path.home() / "imperial_network" / "commodity_cache"
CACHE.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14)"}

def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=20).read())

def get_html(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="ignore")

# ---- Gold via goldprice.dev ----
def gold_spot():
    try:
        d = get_json("https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT")
        return float(d["symbols"][0]["price"])
    except Exception as e:
        print(f"gold: {e}"); return None

# ---- Silver/Platinum/etc via Yahoo Finance ----
YAHOO = {
    "silver":    "SI=F",
    "platinum":  "PL=F",
    "palladium": "PA=F",
    "copper":    "HG=F",
    "crude_oil": "CL=F",
}
def yahoo(sym):
    try:
        d = get_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}")
        return d["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception as e:
        print(f"yahoo {sym}: {e}"); return None

# ---- FX ----
def zar_rate():
    try:
        return get_json("https://api.frankfurter.app/latest?from=USD&to=ZAR")["rates"]["ZAR"]
    except Exception as e:
        print(f"zar: {e}"); return None

# ---- Lithium + Cobalt via Trading Economics scrape ----
def te_price(commodity):
    """Scrape current price from Trading Economics commodity page."""
    try:
        html = get_html(f"https://tradingeconomics.com/commodity/{commodity}")
        # Primary pattern: id="p"
        m = re.search(r'id="p"[^>]*>([\d,.]+)', html)
        if m:
            return float(m.group(1).replace(",", ""))
        # Fallback
        m = re.search(r'>(\d{3,6}\.\d+)<', html)
        if m:
            return float(m.group(1))
    except Exception as e:
        print(f"TE {commodity}: {e}")
    return None

# ---- Fetch ----
gold = gold_spot()
zar  = zar_rate()
metals = {n: yahoo(s) for n, s in YAHOO.items()}
metals = {k: v for k, v in metals.items() if v is not None}
lithium = te_price("lithium")
cobalt  = te_price("cobalt")

print(f"Gold: {gold}")
print(f"USD/ZAR: {zar}")
for k, v in metals.items(): print(f"{k}: {v}")
print(f"Lithium: {lithium}")
print(f"Cobalt: {cobalt}")

# ---- Build Prometheus metrics ----
lines = ["# TYPE sadc_commodity_price gauge"]

if gold:
    lines.append(f'sadc_commodity_price{{commodity="gold",currency="USD",unit="oz",source="goldprice.dev"}} {gold}')
    if zar: lines.append(f'sadc_commodity_price{{commodity="gold",currency="ZAR",unit="oz",source="goldprice.dev"}} {gold*zar:.2f}')

for name, price in metals.items():
    unit = "bbl" if name == "crude_oil" else ("lb" if name == "copper" else "oz")
    lines.append(f'sadc_commodity_price{{commodity="{name}",currency="USD",unit="{unit}",source="yahoo"}} {price}')
    if zar:
        lines.append(f'sadc_commodity_price{{commodity="{name}",currency="ZAR",unit="{unit}",source="yahoo"}} {price*zar:.2f}')

if lithium:
    lines.append(f'sadc_commodity_price{{commodity="lithium",currency="USD",source="tradingeconomics"}} {lithium}')
    if zar:
        lines.append(f'sadc_commodity_price{{commodity="lithium",currency="ZAR",source="tradingeconomics"}} {lithium*zar:.2f}')

if cobalt:
    lines.append(f'sadc_commodity_price{{commodity="cobalt",currency="USD",source="tradingeconomics"}} {cobalt}')
    if zar:
        lines.append(f'sadc_commodity_price{{commodity="cobalt",currency="ZAR",source="tradingeconomics"}} {cobalt*zar:.2f}')

if zar:
    lines.append(f'sadc_fx_rate{{pair="USDZAR"}} {zar}')

# ---- Push ----
body = "\n".join(lines) + "\n"
print("\n--- Push body ---")
print(body)

url = f"{PUSHGATEWAY}/metrics/job/{JOB}/instance/phone"
r = subprocess.run(
    ["curl","-s","-o","/dev/null","-w","%{http_code}",
     "-X","POST",url,"-H","User-Agent: Mozilla/5.0",
     "--data-binary", body],
    capture_output=True, text=True,
)
print(f"Push: {r.stdout.strip()}")
