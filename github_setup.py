"""GitHub 仓库与 Pages 配置工具（凭证取自 Windows 凭证管理器，经 git credential fill）。

用法:
  python github_setup.py create   # 创建仓库（优先 "CCTV News article"，非法名自动回退 CCTV-News-article）
  python github_setup.py pages    # 启用 GitHub Pages（main 分支 / 根目录）
  python github_setup.py status   # 查看 Pages 构建状态
"""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

API = "https://api.github.com"
REPO_NAME_PREFERRED = "CCTV News article"
REPO_NAME_FALLBACK = "CCTV-News-article"


def get_token() -> str:
    import os
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    r = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, timeout=30, env=env,
    )
    for line in r.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"未能从 git credential 获取 GitHub 凭证（stderr: {r.stderr.strip()[:120]}）")


def api(method: str, path: str, token: str, payload: dict | None = None):
    req = urllib.request.Request(
        API + path, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"token {token}",
            "User-Agent": "xwlb-site-setup",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"message": body[:200]}


def owner_login(token: str) -> str:
    code, data = api("GET", "/user", token)
    if code != 200:
        raise SystemExit(f"凭证无效或网络失败：HTTP {code} {data.get('message', '')}")
    print(f"GitHub 账号: {data['login']} (id={data['id']})")
    return data["login"]


def create(token: str):
    login = owner_login(token)
    for name in (REPO_NAME_PREFERRED, REPO_NAME_FALLBACK):
        code, data = api("POST", "/user/repos", token, {
            "name": name,
            "description": "《新闻联播》文字稿逐日存档（2002-2026），Markdown 格式，GitHub Pages 站点。非官方整理。",
            "private": False,
            "has_wiki": False,
            "auto_init": False,
        })
        if code == 201:
            print(f"仓库已创建: {data['full_name']}  {data['html_url']}")
            print(f"PAGES_BASEURL=/{data['name']}")
            return data["name"]
        msg = json.dumps(data, ensure_ascii=False)[:300]
        print(f"[{name}] HTTP {code}: {msg}")
        if code == 422 and "already exists" in msg:
            print(f"仓库已存在: {login}/{name}")
            print(f"PAGES_BASEURL=/{name}")
            return name
    raise SystemExit("仓库创建失败")


def pages(token: str):
    login = owner_login(token)
    repo = resolve_repo(token, login)
    code, data = api("POST", f"/repos/{login}/{repo}/pages", token,
                     {"source": {"branch": "main", "path": "/"}})
    if code in (201, 204):
        print(f"GitHub Pages 已启用（main / 根目录），构建后地址: https://{login}.github.io/{repo}/")
    elif code == 409:
        print("GitHub Pages 已启用过（409），继续")
    else:
        raise SystemExit(f"启用 Pages 失败：HTTP {code} {json.dumps(data, ensure_ascii=False)[:300]}")


def status(token: str):
    login = owner_login(token)
    repo = resolve_repo(token, login)
    code, data = api("GET", f"/repos/{login}/{repo}/pages", token)
    if code != 200:
        raise SystemExit(f"查询 Pages 失败：HTTP {code} {data.get('message', '')}")
    print(f"site: {data.get('html_url')}  status: {data.get('status')}")
    code, b = api("GET", f"/repos/{login}/{repo}/pages/builds/latest", token)
    if code == 200:
        print(f"latest build: {b.get('status')}  created: {b.get('created_at')}"
              + (f"  error: {b.get('error', {}).get('message')}" if b.get("error") else ""))


def resolve_repo(token: str, login: str) -> str:
    # GitHub 会把仓库名中的空格规范化为连字符，优先探测回退名
    from urllib.parse import quote
    for name in (REPO_NAME_FALLBACK, REPO_NAME_PREFERRED):
        code, _ = api("GET", f"/repos/{login}/{quote(name)}", token)
        if code == 200:
            return name
    raise SystemExit("找不到仓库，请先运行 create")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    tk = get_token()
    if cmd == "create":
        create(tk)
    elif cmd == "pages":
        pages(tk)
    elif cmd == "status":
        status(tk)
    else:
        raise SystemExit(__doc__)
