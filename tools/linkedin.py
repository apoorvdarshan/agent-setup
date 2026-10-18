#!/usr/bin/env python3
"""Post to your own LinkedIn profile through the official API.

Credentials live in the macOS Keychain (account = $USER):
  linkedin-client-id      app Client ID
  linkedin-client-secret  app Client Secret
  linkedin-access-token   member access token (~60 days)
  linkedin-member         JSON: {sub, name, expires_at}

Usage:
  linkedin.py auth                      sign in (prints a URL, catches the redirect)
  linkedin.py status                    show who is signed in and token expiry
  linkedin.py post "text" [--yes]       publish a post to your profile
"""
import datetime
import getpass
import http.server
import json
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

REDIRECT_URI = "http://localhost:8765/callback"
PORT = 8765
SCOPES = "openid profile email w_member_social"
AUTH_TIMEOUT = 600  # seconds to wait for the browser redirect
USER = getpass.getuser()


def kc_get(service):
    r = subprocess.run(
        ["security", "find-generic-password", "-a", USER, "-s", service, "-w"],
        capture_output=True, text=True,
    )
    return r.stdout.strip() if r.returncode == 0 else None


def kc_set(service, value, label):
    subprocess.run(
        ["security", "add-generic-password", "-U", "-a", USER, "-s", service, "-l", label, "-w", value],
        check=True, capture_output=True,
    )


def http_json(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return resp.status, dict(resp.headers), (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            body = json.loads(body)
        except ValueError:
            pass
        return e.code, dict(e.headers), body


def require(service, what):
    value = kc_get(service)
    if not value:
        sys.exit(f"Missing {what} in Keychain (service '{service}').")
    return value


def cmd_auth():
    client_id = require("linkedin-client-id", "Client ID")
    client_secret = require("linkedin-client-secret", "Client Secret")
    state = secrets.token_urlsafe(24)
    url = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "scope": SCOPES,
    })
    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return
            q = urllib.parse.parse_qs(parsed.query)
            if q.get("state", [""])[0] != state:
                result["error"] = "state mismatch (ignored a stale or forged redirect)"
            elif "error" in q:
                result["error"] = q.get("error_description", q["error"])[0]
            else:
                result["code"] = q.get("code", [""])[0]
            ok = "code" in result
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = "Signed in. You can close this tab." if ok else "Sign-in failed: " + result.get("error", "")
            self.wfile.write(f"<h2 style='font-family:sans-serif'>{msg}</h2>".encode())

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    server.timeout = 5
    print("Open this URL to sign in:\n" + url, flush=True)
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    deadline = time.time() + AUTH_TIMEOUT
    while not result and time.time() < deadline:
        server.handle_request()
    server.server_close()
    if "code" not in result:
        sys.exit("Sign-in failed: " + result.get("error", "timed out waiting for the redirect"))

    status, _, token = http_json(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data=urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": result["code"],
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        }).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if status != 200 or "access_token" not in token:
        err = token.get("error_description", token) if isinstance(token, dict) else token
        sys.exit(f"Token exchange failed ({status}): {err}")
    access = token["access_token"]
    expires_at = int(time.time()) + int(token.get("expires_in", 0))
    kc_set("linkedin-access-token", access, "LinkedIn access token")

    status, _, me = http_json("https://api.linkedin.com/v2/userinfo",
                              headers={"Authorization": f"Bearer {access}"})
    if status != 200 or "sub" not in me:
        sys.exit(f"Token saved, but profile lookup failed ({status}): {me}")
    kc_set("linkedin-member",
           json.dumps({"sub": me["sub"], "name": me.get("name", ""), "expires_at": expires_at}),
           "LinkedIn member info")
    print(f"Signed in as {me.get('name', me['sub'])}. Token expires {fmt(expires_at)}.")


def fmt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def load_session():
    access = require("linkedin-access-token", "access token (run: linkedin.py auth)")
    member = json.loads(require("linkedin-member", "member info (run: linkedin.py auth)"))
    if member["expires_at"] <= time.time():
        sys.exit(f"Token expired {fmt(member['expires_at'])}. Run: linkedin.py auth")
    return access, member


def cmd_status():
    access, member = load_session()
    status, _, me = http_json("https://api.linkedin.com/v2/userinfo",
                              headers={"Authorization": f"Bearer {access}"})
    days = int((member["expires_at"] - time.time()) // 86400)
    live = "valid" if status == 200 else f"rejected ({status})"
    print(f"{member['name']} — token {live}, expires {fmt(member['expires_at'])} ({days} days left)")


RESERVED = re.compile(r"([\\|{}@\[\]()<>#*_~])")


def to_little_text(text):
    """Escape LinkedIn's reserved characters, keeping #hashtags clickable."""
    out, pos = [], 0
    for m in re.finditer(r"(?<![\w#])#(\w+)", text):
        out.append(RESERVED.sub(r"\\\1", text[pos:m.start()]))
        out.append("{hashtag|\\#|" + m.group(1) + "}")
        pos = m.end()
    out.append(RESERVED.sub(r"\\\1", text[pos:]))
    return "".join(out)


def api_version():
    # Versions are monthly and supported for a year; two months back is always live.
    d = datetime.date.today().replace(day=1)
    for _ in range(2):
        d = (d - datetime.timedelta(days=1)).replace(day=1)
    return d.strftime("%Y%m")


def cmd_post(text, yes):
    access, member = load_session()
    if not text.strip():
        sys.exit("Post text is empty.")
    if not yes:
        print(f"--- Posting publicly as {member['name']} ---\n{text}\n---")
        if input("Post this? [y/N] ").strip().lower() != "y":
            sys.exit("Cancelled.")
    status, headers, body = http_json(
        "https://api.linkedin.com/rest/posts",
        data=json.dumps({
            "author": f"urn:li:person:{member['sub']}",
            "commentary": to_little_text(text),
            "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [],
                             "thirdPartyDistributionChannels": []},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }).encode(),
        headers={
            "Authorization": f"Bearer {access}",
            "Content-Type": "application/json",
            "LinkedIn-Version": api_version(),
            "X-Restli-Protocol-Version": "2.0.0",
        },
        method="POST",
    )
    if status != 201:
        sys.exit(f"Post failed ({status}): {body}")
    urn = {k.lower(): v for k, v in headers.items()}.get("x-restli-id", "")
    print(f"Posted: https://www.linkedin.com/feed/update/{urn}/")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    if args[0] == "auth":
        cmd_auth()
    elif args[0] == "status":
        cmd_status()
    elif args[0] == "post" and len(args) == 2:
        cmd_post(args[1], "--yes" in sys.argv)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
