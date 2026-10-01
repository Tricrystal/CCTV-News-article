# CCTV News article（《新闻联播》文字稿存档）

中央电视台《新闻联播》文字稿的逐日 Markdown 存档，**在线阅读**：
<https://tricrystal.github.io/CCTV-News-article/>

每期节目一篇 Markdown 文件，收录当日全部新闻条目（标题 + 正文），按播出顺序排列。

## 数据覆盖

| 年份范围 | 说明 |
|---|---|
| 2002-09-30 ~ 2009-06-30 | 央视网旧版目录页存档（`www.cctv.com/news/xwlb/`），详情页部分失效，失效条目仅存标题 |
| 2009-07-01 ~ 2010-05-09 | 央视网旧版文字稿索引页，文章页部分失效 |
| 2010-05-10 ~ 2016-02-02 | cntv 时代列表页，存档零星 |
| 2016-02-03 ~ 至今 | 现行 day 列表页，正文完整 |

> 抓取仍在进行中的年份会随抓取进度更新；重新生成方式见下文。

## 目录结构

```
├── index.md              # 首页（年份列表，GitHub Pages 入口）
├── {年}/index.md         # 该年逐日目录
├── {年}/新闻联播_YYYYMMDD.md   # 每期一篇
├── _config.yml           # Jekyll 站点配置
├── _layouts/default.html # 站点模板
├── convert_to_md.py      # 文稿 JSON → Markdown 转换脚本
└── github_setup.py       # 仓库 / Pages 配置脚本
```

## 重新生成

文稿原始 JSON（`新闻联播_YYYYMMDD.txt`）由爬虫产出后，运行：

```bash
python convert_to_md.py    # 重新扫描来源目录，全量重建 Markdown
git add -A && git commit -m "更新文稿" && git push   # 推送后 Pages 自动重新构建
```

## 来源与声明

- 文稿抓取自央视网历史存档页面（爬虫工程见另仓），本站为非官方整理，仅供学习研究；
- 内容版权归中央电视台所有，如有侵权请联系删除。
