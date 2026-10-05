#!/usr/bin/env python3
"""Pull Cloudflare metrics from the Worker and refresh the local DB table."""
import json, os, subprocess, sys, urllib.request

WORKER = "https://cloudflare-prometheus-exporter.getfriendhumbulani30.workers.dev/metrics"
DB = "imperial_nexus"
SOCK = os.path.expanduser("~/mysql_run/mysql.sock")

def get_password():
    try:
        with open(os.path.expanduser("~/.bashrc")) as f:
            for line in f:
                if line.startswith("export MYSQL_ROOT_PASSWORD="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""

def fetch_metrics():
    req = urllib.request.Request(WORKER, headers={"User-Agent": "cf-refresh/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def parse_prometheus(text):
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            head, value = line.rsplit(" ", 1)
        except ValueError:
            continue
        if "{" in head:
            name, rest = head.split("{", 1)
            label_part = rest.rstrip("}")
            labels = {}
            for pair in label_part.split(","):
                if "=" not in pair:
                    continue
                k, v = pair.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"')
                if k in ("__name__", "job", "instance", "exported_job", "exported_instance"):
                    continue
                labels[k] = v
        else:
            name = head
            labels = {}
        yield name.strip(), value.strip(), labels

def push_to_db(rows):
    if not rows:
        print("no rows to push")
        return
    pwd = get_password()
    cmd = ["mariadb", "-u", "root", "-S", SOCK]
    if pwd:
        cmd.append("-p" + pwd)
    cmd.extend([DB])

    sql = ["DELETE FROM cloudflare_metrics WHERE timestamp > DATE_SUB(NOW(), INTERVAL 7 DAY);"]
    for metric, value, labels in rows:
        try:
            float(value)
        except ValueError:
            continue
        labels_json = json.dumps(labels, separators=(",", ":"))
        labels_json = labels_json.replace("'", "''")
        sql.append(
            "INSERT INTO cloudflare_metrics (metric, value, labels, timestamp) "
            f"VALUES ('{metric}', {value}, '{labels_json}', NOW());"
        )
    script = "\n".join(sql)
    res = subprocess.run(cmd, input=script, capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        print("DB ERROR:", res.stderr.strip(), file=sys.stderr)
        sys.exit(1)
    print(f"inserted {len(rows)} rows")

def main():
    try:
        raw = fetch_metrics()
    except Exception as e:
        print("fetch failed:", e, file=sys.stderr)
        sys.exit(1)
    push_to_db(list(parse_prometheus(raw)))

if __name__ == "__main__":
    main()
