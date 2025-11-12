import argparse, os, sys, smtplib, pathlib, mimetypes
from email.message import EmailMessage

def env(name, required=True, default=None):
    v = os.getenv(name, default)
    if required and not v:
        print(f"[ERROR] Missing env var: {name}", file=sys.stderr)
        sys.exit(2)
    return v

def attach(msg, path):
    p = pathlib.Path(path)
    ctype, _ = mimetypes.guess_type(str(p))
    maintype, subtype = (ctype.split('/',1) if ctype else ("application","octet-stream"))
    with open(p, "rb") as f:
        msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=p.name)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body", required=True)
    ap.add_argument("--to", required=True, help="Comma-separated")
    ap.add_argument("--attach", nargs="*", default=[])
    args = ap.parse_args()

    host = env("SMTP_HOST")
    port = int(env("SMTP_PORT", default="587", required=False))
    user = env("SMTP_USER")
    pwd  = env("SMTP_PASS")
    sender = env("REPORT_FROM")

    msg = EmailMessage()
    msg["Subject"] = args.subject
    msg["From"] = sender
    msg["To"] = [x.strip() for x in args.to.split(",") if x.strip()]
    msg.set_content(args.body)

    for a in args.attach:
        if a: attach(msg, a)

    with smtplib.SMTP(host, port, timeout=60) as s:
        s.starttls()
        s.login(user, pwd)
        s.send_message(msg)

    print("[OK] Email sent.")

if __name__ == "__main__":
    main()
