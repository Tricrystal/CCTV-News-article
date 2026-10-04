"""将《新闻联播》文字稿 JSON 文本（新闻联播_YYYYMMDD.txt）转换为 Jekyll 站点的 Markdown 页面。

输入：SOURCE_DIRS 下按 {年}/新闻联播_YYYYMMDD.txt 组织的 JSON 文件
      （key=新闻标题、value=正文，条目按播出顺序排列）
输出：本目录（站点仓库根）下
      {年}/新闻联播_YYYYMMDD.md   每期一篇，条目为二级标题 + 段落正文
      {年}/index.md               该年目录页
      index.md                    全站首页（年份列表）

同名日期存在于多个来源目录时，自动保留条目更全的一份（按非空正文数、条目数排序）。

用法: python convert_to_md.py
"""
import json
import os
import re
import sys
from collections import defaultdict

# ====================== 配置区域 ======================
SOURCE_DIRS = [
    r"Y:\新闻联播文稿",        # xwlb.py 抓取（2009-07-01 起）
    r"Y:\xwlb\新闻联播文稿",   # xwlb_pre2009.py 抓取（2002-09-30 ~ 2009-06-30）
]
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_TITLE = "新闻联播文字稿"
FILE_RE = re.compile(r"^新闻联播_(\d{8})\.txt$")


def fmt_date_cn(date_str: str) -> str:
    return f"{int(date_str[:4])}年{int(date_str[4:6])}月{int(date_str[6:8])}日"


def load_sources():
    """扫描所有来源目录，返回 {date: (path, content_dict)}，按内容完整度去重"""
    best = {}
    for src in SOURCE_DIRS:
        if not os.path.isdir(src):
            print(f"[warn] 来源目录不存在：{src}")
            continue
        for year in sorted(os.listdir(src)):
            year_dir = os.path.join(src, year)
            if not os.path.isdir(year_dir):
                continue
            for name in os.listdir(year_dir):
                m = FILE_RE.match(name)
                if not m:
                    continue
                path = os.path.join(year_dir, name)
                try:
                    with open(path, encoding="utf-8") as f:
                        content = json.load(f)
                except Exception as e:
                    print(f"[warn] JSON 解析失败，跳过 {path}: {e}")
                    continue
                if not isinstance(content, dict):
                    continue
                date = m.group(1)
                score = (sum(1 for v in content.values() if v.strip()), len(content))
                if date not in best or score > best[date][0]:
                    best[date] = (score, path, content)
    return {d: (p, c) for d, (s, p, c) in best.items()}


def body_to_markdown(body: str) -> str:
    """正文按行拆为段落（空行分隔）；正文为空时给出缺失说明"""
    body = body.strip()
    if not body:
        return "（正文缺失：原文字稿网页已失效，仅存标题。）"
    paras = [ln.strip() for ln in body.split("\n") if ln.strip()]
    return "\n\n".join(paras)


# 标题末尾的站点名后缀（cntv 时代与现行官网模板），仅作显示层清理，不改源数据
TITLE_SUFFIX_RE = re.compile(r"_(?:新闻台_中国网络电视台|CCTV节目官网-.*|央视网(?:\([^)]*\))?|中国网络电视台)$")


def title_display(title: str) -> str:
    t = TITLE_SUFFIX_RE.sub("", title.strip()).strip()
    return t


def title_to_markdown(title: str) -> str:
    # 防止以 # 开头的标题被解析为标题层级
    t = title_display(title)
    if t.startswith("#"):
        t = "\\" + t
    return t


def write_md(path: str, front: dict, body: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("---\n")
        for k, v in front.items():
            f.write(f'{k}: "{v}"\n')
        f.write("---\n\n")
        f.write(body.rstrip() + "\n")


def convert():
    by_date = load_sources()
    print(f"共读取 {len(by_date)} 天的文稿")

    by_year = defaultdict(list)  # year -> [(date, n_items)]
    for date, (path, content) in sorted(by_date.items()):
        year = date[:4]
        by_year[year].append((date, len(content)))
        date_cn = fmt_date_cn(date)
        parts = [
            f"# {SITE_TITLE} · {date_cn}",
            "",
            f"> 共 {len(content)} 条新闻 · 央视网《新闻联播》{date_cn}播出 · [← {year} 年目录](./) · [首页](../)",
            "",
        ]
        for title, body in content.items():
            parts.append(f"## {title_to_markdown(title)}")
            parts.append("")
            parts.append(body_to_markdown(body))
            parts.append("")
        write_md(
            os.path.join(OUT_DIR, year, f"新闻联播_{date}.md"),
            {"layout": "default", "title": f"{SITE_TITLE}（{date_cn}）"},
            "\n".join(parts),
        )

    # 每年目录页 {year}/index.md
    for year, days in sorted(by_year.items()):
        days.sort()
        lines = [
            f"# {year} 年节目目录",
            "",
            f"共 {len(days)} 期（{fmt_date_cn(days[0][0])} ~ {fmt_date_cn(days[-1][0])}）。[← 返回首页](../)",
            "",
        ]
        for date, n in days:
            d = f"{int(date[4:6])}月{int(date[6:8])}日"
            lines.append(f"- [{d}]({date_filename(date)})（{n} 条）")
        write_md(
            os.path.join(OUT_DIR, year, "index.md"),
            {"layout": "default", "title": f"{year} 年目录"},
            "\n".join(lines),
        )

    # 首页 index.md
    lines = [
        f"# {SITE_TITLE}",
        "",
        "中央电视台《新闻联播》文字稿存档，逐日收录每期节目的全部条目（标题与正文），按播出顺序排列。",
        "",
        "数据来源：央视网历史存档页面（2002-09-30 起），由爬虫逐日抓取、脚本转换为 Markdown。",
        "",
        "## 按年份浏览",
        "",
    ]
    for year in sorted(by_year):
        days = by_year[year]
        span = f"{fmt_date_cn(days[0][0])} ~ {fmt_date_cn(days[-1][0])}" if len(days) > 1 else fmt_date_cn(days[0][0])
        lines.append(f"- [{year} 年]({year}/)（{len(days)} 期，{span}）")
    write_md(
        os.path.join(OUT_DIR, "index.md"),
        {"layout": "default", "title": SITE_TITLE},
        "\n".join(lines),
    )

    total_md = sum(len(v) for v in by_year.values())
    print(f"已生成：{total_md} 篇日稿 + {len(by_year)} 个年份目录页 + 首页 index.md")


def date_filename(date: str) -> str:
    from urllib.parse import quote
    return quote(f"新闻联播_{date}.html")


if __name__ == "__main__":
    sys.exit(convert())
