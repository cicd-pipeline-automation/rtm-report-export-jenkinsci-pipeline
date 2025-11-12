import argparse, os, sys, json, pathlib, requests

def env(name, required=True, default=None):
    v = os.getenv(name, default)
    if required and not v:
        print(f"[ERROR] Missing env var: {name}", file=sys.stderr)
        sys.exit(2)
    return v

def get_page(base, auth, space, title):
    url = f"{base.rstrip('/')}/rest/api/content"
    params = {"spaceKey": space, "title": title, "expand": "version"}
    r = requests.get(url, params=params, auth=auth, timeout=60)
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None

def create_page(base, auth, space, title, body_html, parent_id=None):
    url = f"{base.rstrip('/')}/rest/api/content"
    data = {
        "type": "page",
        "title": title,
        "space": {"key": space},
        "body": {"storage": {"value": body_html, "representation": "storage"}},
    }
    if parent_id:
        data["ancestors"] = [{"id": str(parent_id)}]
    r = requests.post(url, json=data, auth=auth, timeout=60)
    r.raise_for_status()
    return r.json()

def update_page(base, auth, page, body_html):
    page_id = page["id"]
    version = page["version"]["number"] + 1
    url = f"{base.rstrip('/')}/rest/api/content/{page_id}"
    data = {
        "id": page_id,
        "type": "page",
        "title": page["title"],
        "version": {"number": version},
        "body": {"storage": {"value": body_html, "representation": "storage"}},
    }
    r = requests.put(url, json=data, auth=auth, timeout=60)
    r.raise_for_status()
    return r.json()

def attach_file(base, auth, page_id, filepath):
    url = f"{base.rstrip('/')}/rest/api/content/{page_id}/child/attachment"
    fpath = pathlib.Path(filepath)
    headers = {"X-Atlassian-Token": "no-check"}
    files = {"file": (fpath.name, open(fpath, "rb"))}
    # Try update (if same filename) else create
    r_get = requests.get(url, auth=auth, timeout=60, params={"filename": fpath.name})
    if r_get.status_code == 200 and r_get.json().get("results"):
        attach_id = r_get.json()["results"][0]["id"]
        url = f"{url}/{attach_id}/data"
    r = requests.post(url, headers=headers, files=files, auth=auth, timeout=120)
    r.raise_for_status()
    return r.json()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", default="", help="Confluence storage-format HTML")
    ap.add_argument("--attach", nargs="*", default=[])
    ap.add_argument("--parent-id", default=None)
    args = ap.parse_args()

    base = env("CONFLUENCE_BASE")
    user = env("CONFLUENCE_USER")
    token = env("CONFLUENCE_TOKEN")
    auth = (user, token)

    page = get_page(base, auth, args.space, args.title)
    if page:
        updated = update_page(base, auth, page, args.body)
        page_id = updated["id"]
    else:
        created = create_page(base, auth, args.space, args.title, args.body, args.parent_id)
        page_id = created["id"]

    for f in args.attach:
        if f:
            print(f"[INFO] Attaching {f}")
            attach_file(base, auth, page_id, f)

    view_link = f"{base.rstrip('/')}/spaces/{args.space}/pages/{page_id}"
    print(f"[OK] Confluence page: {view_link}")
    print(f"CONFLUENCE_PAGE_URL={view_link}")

if __name__ == "__main__":
    main()
