"""
Deploy PHP app to VPS via SSH/SFTP using paramiko.
"""
import os, sys
from pathlib import Path
from dotenv import load_dotenv
import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

HOST   = os.getenv("SXSRATIM_HOST", "")
PORT   = int(os.getenv("SXSRATIM_PORT", "22"))
USER   = os.getenv("SXSRATIM_USER", "")
PASSWD = os.getenv("SXSRATIM_PASS", "")
FOLDER = os.getenv("SXSRATIM_FOLDER", "chat-summary")

BASE = Path(__file__).resolve().parent

FILES = [
    "index.php",
    "prompts.php",
    "prompts_config.php",
    ".htaccess",
    "templates/index.html",
    "static/app.js",
    "static/styles.css",
    "data/dialogues.json",
]


def run(ssh, cmd, desc=""):
    label = desc or cmd[:70]
    print(f"  >> {label}")
    _, stdout, stderr = ssh.exec_command(cmd, get_pty=False)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out: print(f"     {out[:400]}")
    if err and not any(x in err.lower() for x in ("warning", "notice", "hint")):
        print(f"  [err] {err[:400]}")
    return out


def mkdir_p(sftp, path):
    parts = path.split("/")
    cur = ""
    for p in parts:
        if not p:
            continue
        cur += "/" + p
        try:
            sftp.stat(cur)
        except FileNotFoundError:
            sftp.mkdir(cur)


def main():
    print(f"Connecting to {USER}@{HOST}:{PORT}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWD, timeout=15)
    print("Connected.")

    web_root = run(ssh, f"echo $HOME", "home dir").strip()
    web_root = web_root + "/" + FOLDER
    print(f"  Target: {web_root}")

    sftp = ssh.open_sftp()

    # Ensure all needed remote dirs exist
    dirs = set()
    for f in FILES:
        d = web_root + "/" + "/".join(f.split("/")[:-1])
        if d.rstrip("/") != web_root:
            dirs.add(d)
    dirs.add(web_root)
    dirs.add(web_root + "/data")
    dirs.add(web_root + "/static")
    dirs.add(web_root + "/templates")
    for d in sorted(dirs):
        mkdir_p(sftp, d)

    # Upload files
    print("Uploading files...")
    for rel in FILES:
        local = BASE / rel
        if not local.exists():
            print(f"  [skip] {rel}")
            continue
        remote = web_root + "/" + rel
        size_kb = local.stat().st_size // 1024
        print(f"  {rel} ({size_kb}KB)")
        sftp.put(str(local), remote)

    sftp.close()
    ssh.close()
    print("\nDone!")
    print(f"  App: https://sexsratim.in/{FOLDER.split('/')[-1]}/")


if __name__ == "__main__":
    main()
