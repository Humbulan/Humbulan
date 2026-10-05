#!/usr/bin/env python3
import os
import pymysql, time, sys, traceback
from huggingface_hub import InferenceClient
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


DB_SOCKET = "/data/data/com.termux/files/home/mysql_run/mysql.sock"
DB_USER = "root"
DB_PASSWORD = _mysql_password()
DB_NAME = "imperial_nexus"

# Use a robust, widely available model
HF_TOKEN = os.environ.get("HUGGINGFACE_API_KEY", "")
MODEL = "meta-llama/Llama-3.3-70B-Instruct:fastest"

def get_conn():
    return pymysql.connect(
        unix_socket=DB_SOCKET,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True
    )

def generate_desc(itype, severity, action):
    prompt = (
        f"Generate a concise description and suggested actions for a community incident of type '{itype}' "
        f"with severity {severity}. Action taken: '{action}'. Keep to 2-3 sentences."
    )
    try:
        client = InferenceClient(token=HF_TOKEN)
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        return completion.choices[0].message.content
    except Exception as e:
        sys.stderr.write(f"LLM error: {e}\n")
        traceback.print_exc(file=sys.stderr)
        return None

def main():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SHOW COLUMNS FROM community_incidents LIKE 'description'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE community_incidents ADD COLUMN description TEXT")
            conn.commit()

        while True:
            cur.execute(
                "SELECT id, incident_type, severity_level, action_taken "
                "FROM community_incidents "
                "WHERE description IS NULL OR description = '' LIMIT 1"
            )
            row = cur.fetchone()
            if row:
                id_, itype, sev, act = row
                desc = generate_desc(itype, sev, act)
                if desc:
                    cur.execute("UPDATE community_incidents SET description = %s WHERE id = %s", (desc, id_))
                    conn.commit()
                    sys.stderr.write(f"Updated incident {id_}\n")
                else:
                    sys.stderr.write(f"Failed to generate description for incident {id_}\n")
            time.sleep(5)
    except Exception as e:
        sys.stderr.write(f"Fatal error: {e}\n")
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    main()
