"""
Deploy app to VPS via SSH/SFTP using paramiko.
"""
import os, sys
from pathlib import Path
from dotenv import load_dotenv
import paramiko

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

HOST   = os.getenv("SXSRATIM_HOST", "")
PORT   = int(os.getenv("SXSRATIM_PORT", "22"))
USER   = os.getenv("SXSRATIM_USER", "")
PASSWD = os.getenv("SXSRATIM_PASS", "")
FOLDER = os.getenv("SXSRATIM_FOLDER", "chat-summary")

BASE = Path(__file__).resolve().parent

FILES = [
    ("app.py",               f"{FOLDER}/app.py"),
    ("requirements.txt",     f"{FOLDER}/requirements.txt"),
    ("templates/index.html", f"{FOLDER}/templates/index.html"),
    ("static/app.js",        f"{FOLDER}/static/app.js"),
    ("static/styles.css",    f"{FOLDER}/static/styles.css"),
    ("data/dialogues.json",  f"{FOLDER}/data/dialogues.json"),
]
if (BASE / "data" / "summaries.json").exists():
    FILES.append(("data/summaries.json", f"{FOLDER}/data/summaries.json"))

APP_ENV_KEYS = ["GROK_API_KEY","GROK_BASE_URL","GROK_MODEL",
                "SUMMARY_CHUNK_SIZE","SUMMARY_MAX_FIELDS_PER_CATEGORY",
                "SUMMARY_MAX_LIST_ITEMS","SUMMARY_MAX_VALUE_LENGTH"]
APP_ENV = "\n".join(f"{k}={os.getenv(k,'')}" for k in APP_ENV_KEYS if os.getenv(k)) + "\n"

NGINX_CONF = f"""server {{
    listen 80;
    server_name {HOST} _;

    client_max_body_size 20M;

    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120;
    }}
}}
"""

def run(ssh, cmd, desc=""):
    label = desc or cmd[:70]
    print(f"  >> {label}")
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=False)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out: print(f"     {out[:300]}")
    if err and not any(x in err.lower() for x in ("warning","notice","hint")):
        print(f"  [err] {err[:300]}")
    return out

def main():
    print(f"Connecting to {USER}@{HOST}:{PORT}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWD, timeout=15)
    print("Connected.")

    home = run(ssh, "echo $HOME", "home dir").strip()
    print(f"  Home: {home}")

    # Detect python
    py = run(ssh, "which python3 || which python || echo NONE", "find python").strip().split("\n")[0]
    pyver = run(ssh, f"{py} --version 2>&1", "python version")
    print(f"  Python: {py} ({pyver})")

    # On CentOS/RHEL without python3, install via epel
    if "2.7" in pyver or "NONE" in py:
        print("  Installing Python 3 via epel...")
        run(ssh, "sudo yum install -y epel-release 2>&1 | tail -3", "install epel")
        run(ssh, "sudo yum install -y python3 python3-pip 2>&1 | tail -3", "install python3")
        py = run(ssh, "which python3", "find python3").strip()
        print(f"  Python3: {py}")

    # Ensure nginx
    nginx_ok = run(ssh, "which nginx || echo NONE", "find nginx").strip()
    if "NONE" in nginx_ok:
        pkg_mgr = run(ssh, "which yum apt-get apk dnf 2>/dev/null | head -1", "find pkg mgr").strip()
        if "yum" in pkg_mgr:
            run(ssh, "sudo yum install -y nginx 2>&1 | tail -3", "install nginx (yum)")
        elif "apt-get" in pkg_mgr:
            run(ssh, "sudo apt-get install -y nginx 2>&1 | tail -3", "install nginx (apt)")
        elif "apk" in pkg_mgr:
            run(ssh, "sudo apk add nginx 2>&1 | tail -3", "install nginx (apk)")

    # Create dirs
    run(ssh, f"mkdir -p {home}/{FOLDER}/data {home}/{FOLDER}/templates {home}/{FOLDER}/static", "create dirs")

    # Upload files
    sftp = ssh.open_sftp()
    print("Uploading files...")
    for local_rel, remote_rel in FILES:
        local = BASE / local_rel
        if not local.exists():
            print(f"  [skip] {local_rel}")
            continue
        remote = f"{home}/{remote_rel}"
        print(f"  {local_rel} ({local.stat().st_size//1024}KB)")
        sftp.put(str(local), remote)

    with sftp.open(f"{home}/{FOLDER}/.env", "w") as f:
        f.write(APP_ENV)
    print("  .env uploaded")

    # nginx config (will be moved by setup.sh)
    with sftp.open("/tmp/chat-summary.nginx", "w") as f:
        f.write(NGINX_CONF)

    # setup script
    setup = f"""#!/bin/bash
set -e
cd {home}/{FOLDER}
# Create venv
if {py} -m venv venv 2>/dev/null; then
    venv/bin/pip install --quiet -r requirements.txt
    GUNICORN={home}/{FOLDER}/venv/bin/gunicorn
else
    {py} -m pip install --user --quiet -r requirements.txt
    GUNICORN=$({py} -m site --user-base)/bin/gunicorn
fi
echo "Gunicorn: $GUNICORN"
# Write final service file
sudo tee /etc/systemd/system/chat-summary.service > /dev/null << SVCEOF
[Unit]
Description=Chat Summary Flask App
After=network.target

[Service]
User={USER}
WorkingDirectory={home}/{FOLDER}
ExecStart=$GUNICORN -w 2 -b 127.0.0.1:8000 app:app
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SVCEOF
sudo systemctl daemon-reload
sudo systemctl enable chat-summary
sudo systemctl restart chat-summary
# nginx setup
if [ -d /etc/nginx/sites-available ]; then
    sudo mv /tmp/chat-summary.nginx /etc/nginx/sites-available/chat-summary
    sudo ln -sf /etc/nginx/sites-available/chat-summary /etc/nginx/sites-enabled/chat-summary
else
    sudo mv /tmp/chat-summary.nginx /etc/nginx/conf.d/chat-summary.conf
fi
sudo nginx -t && sudo systemctl enable nginx && sudo systemctl reload nginx
echo "DEPLOY OK"
"""
    with sftp.open(f"{home}/{FOLDER}/setup.sh", "w") as f:
        f.write(setup)
    sftp.close()

    run(ssh, f"chmod +x {home}/{FOLDER}/setup.sh && bash {home}/{FOLDER}/setup.sh 2>&1", "setup & start")

    status = run(ssh, "sudo systemctl is-active chat-summary", "service status")
    print(f"\nService: {status}")

    # Get public IP
    ip = run(ssh, "curl -s ifconfig.me || echo unknown", "public ip")
    ssh.close()

    print(f"\nDone!")
    print(f"  App: http://{ip}/")
    print(f"  Or:  http://{HOST}/")

if __name__ == "__main__":
    main()
