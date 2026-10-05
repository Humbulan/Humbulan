import os
import sys, json, subprocess, datetime
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


def run_mysql(query):
    cmd = ['mariadb', '-u', 'root', '-p' + _mysql_password(), '-S', '/data/data/com.termux/files/home/mysql_run/mysql.sock', '-e', query]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0: return None
    lines = result.stdout.strip().split('\n')
    if len(lines) < 2: return None
    return lines[1].split('\t')[0]

def get_metrics():
    payments = run_mysql("USE imperial_nexus; SELECT COUNT(*) FROM payment;")
    users = run_mysql("USE imperial_nexus; SELECT COUNT(*) FROM users;")
    villages = run_mysql("USE imperial_nexus; SELECT COUNT(*) FROM villages;")
    sectors = run_mysql("USE imperial_nexus; SELECT COUNT(*) FROM system_sectors;")
    pending = run_mysql("USE imperial_nexus; SELECT COUNT(*) FROM payment WHERE status='pending';")
    ussd_sessions = run_mysql("USE imperial_nexus; SELECT COUNT(*) FROM ussd_session;")
    orders = run_mysql("USE imperial_nexus; SELECT COUNT(*) FROM orders;")
    revenue = run_mysql("USE imperial_nexus; SELECT SUM(amount) FROM payment WHERE status='success';")
    village_target = run_mysql("USE imperial_nexus; SELECT value FROM settings WHERE \`key\`='village_target';")
    if village_target is None: village_target = "120"
    
    active_risks = run_mysql("USE imperial_nexus; SELECT COUNT(*) FROM municipal_governance_risks WHERE risk_level IN ('high', 'critical');")
    open_tenders = run_mysql("USE imperial_nexus; SELECT COUNT(*) FROM tender_monitor WHERE status = 'open';")

    portfolio_value = run_mysql("USE imperial_nexus; SELECT IFNULL(SUM(amount), 0) FROM payment WHERE status='success';")
    if portfolio_value is None: portfolio_value = "0"
    gain_value = "238050000"
    try:
        true_valuation = str(float(portfolio_value) + float(gain_value))
    except:
        true_valuation = "0"

    sadc_corridor = "ACTIVE"
    wealth_lock = "ACTIVE"
    last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "portfolio_value": portfolio_value,
        "gain_value": gain_value,
        "true_valuation": true_valuation,
        "sadc_corridor": sadc_corridor,
        "wealth_lock": wealth_lock,
        "last_updated": last_updated,
        "payments": payments,
        "users": users,
        "villages": villages,
        "village_target": int(village_target),
        "system_sectors": sectors,
        "pending_payments": pending,
        "total_ussd_sessions": ussd_sessions,
        "total_orders": orders,
        "total_revenue": revenue,
        "active_risks": int(active_risks) if active_risks else 0,
        "open_tenders": int(open_tenders) if open_tenders else 0
    }

if __name__ == "__main__":
    print(json.dumps(get_metrics(), indent=2))
