import argparse, os, sys, pathlib, mimetypes
import requests

def env(name, required=True, default=None):
    v = os.getenv(name, default)
    if required and not v:
        print(f"[ERROR] Missing env var: {name}", file=sys.stderr)
        sys.exit(2)
    return v

def build_export_url(base, template, project, test_exec, fmt):
    # Allow {base}, {project}, {test_exec}, {format} in template
    return template.format(base=base.rstrip("/"),
                           project=project,
                           test_exec=test_exec,
                           format=fmt)

def infer_extension(content_type, fallback):
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ext
        if "pdf" in content_type: return ".pdf"
        if "html" in content_type or "text" in content_type: return ".html"
    return fallback

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rtm-project", required=True)
    ap.add_argument("--test-exec", required=True)
    ap.add_argument("--format", default="html", choices=["html","pdf"])
    ap.add_argument("--outdir", default="report")
    args = ap.parse_args()

    jira_base = env("JIRA_BASE")
    jira_user = env("JIRA_USER")
    jira_token = env("JIRA_TOKEN")
    template  = env("RTM_EXPORT_URL_TEMPLATE")

    url = build_export_url(jira_base, template, args.rtm_project, args.test_exec, args.format)
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Requesting RTM export: {url}")
    r = requests.get(url, auth=(jira_user, jira_token), timeout=120)
    if r.status_code != 200:
        print(f"[ERROR] RTM export failed: {r.status_code} {r.text[:500]}", file=sys.stderr)
        sys.exit(3)

    ctype = r.headers.get("Content-Type", "")
    # Default filenames
    base = f"rtm_report_{args.rtm_project}_{args.test_exec}".replace("/","-")
    ext = infer_extension(ctype, f".{args.format}")
    outfile = outdir / f"{base}{ext}"
    with open(outfile, "wb") as f:
        f.write(r.content)

    # If you also want a sibling HTML or PDF and only one was returned,
    # you could add conversion here (optional, left minimal by design).

    # For Jenkins artifact paths:
    print(f"[OK] Saved: {outfile}")
    print(f"ARTIFACT_PATH={outfile}")  # parsable output for pipeline

if __name__ == "__main__":
    main()
