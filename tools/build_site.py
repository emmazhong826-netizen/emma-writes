from pathlib import Path
import argparse
import html
import json
import re
import shutil
import sys

try:
    import markdown
except ImportError:
    print("ERROR: Python package 'markdown' is not installed.")
    print("Run: python3 -m pip install markdown")
    sys.exit(1)


ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
PREVIEW_DIR = ROOT / "_site_preview"

WRITING_DIR = CONTENT_DIR / "writing"
WORK_DIR = CONTENT_DIR / "work"

CATEGORY_LABELS = {
    "essay": "杂记",
    "prose": "散文",
    "reading": "读后感",
    "commentary": "社会评论",
    "poem": "诗歌",
}

CATEGORY_ORDER = [
    "essay",
    "prose",
    "reading",
    "commentary",
    "poem",
]


# =========================================================
# FRONT MATTER
# =========================================================

def parse_scalar(value):
    value = value.strip()

    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {'"', "'"}
    ):
        value = value[1:-1]

    value = value.replace('\\"', '"')
    value = value.replace("\\\\", "\\")

    if value.lower() == "true":
        return True

    if value.lower() == "false":
        return False

    if re.fullmatch(r"-?\d+", value):
        try:
            return int(value)
        except ValueError:
            pass

    return value


def read_markdown_file(path):
    text = path.read_text(encoding="utf-8")

    if not text.startswith("---\n"):
        raise ValueError(
            f"{path}: missing YAML-style front matter"
        )

    parts = text.split("\n---\n", 1)

    if len(parts) != 2:
        raise ValueError(
            f"{path}: front matter is not closed with ---"
        )

    raw_meta = parts[0][4:]
    body = parts[1].lstrip("\n")

    meta = {}

    for line in raw_meta.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)

        meta[key.strip()] = parse_scalar(
            value
        )

    meta["_source_path"] = path
    meta["_body_markdown"] = body
    meta["_slug"] = str(
        meta.get("slug")
        or path.stem
    )

    return meta


# =========================================================
# TEXT HELPERS
# =========================================================

def date_sort_key(value):
    value = str(
        value or ""
    ).strip()

    nums = [
        int(x)
        for x in re.findall(
            r"\d+",
            value
        )
    ]

    if not nums:
        return (0, 0, 0)

    year = nums[0]
    month = (
        nums[1]
        if len(nums) >= 2
        else 0
    )
    day = (
        nums[2]
        if len(nums) >= 3
        else 0
    )

    return (
        year,
        month,
        day
    )


def display_date(value):
    value = str(
        value or ""
    ).strip()

    match = re.fullmatch(
        r"(\d{4})-(\d{2})-(\d{2})",
        value
    )

    if match:
        y, m, d = match.groups()

        return (
            f"{int(y)}. "
            f"{int(m)}. "
            f"{int(d)}"
        )

    return value


def strip_markdown(md):
    text = md

    text = re.sub(
        r"```.*?```",
        " ",
        text,
        flags=re.S
    )

    text = re.sub(
        r"`([^`]*)`",
        r"\1",
        text
    )

    text = re.sub(
        r"!\[([^\]]*)\]\([^)]+\)",
        r"\1",
        text
    )

    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    text = re.sub(
        r"^#{1,6}\s*",
        "",
        text,
        flags=re.M
    )

    text = re.sub(
        r"^[>\-*+]\s*",
        "",
        text,
        flags=re.M
    )

    text = re.sub(
        r"[*_~]",
        "",
        text
    )

    text = html.unescape(
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def md_to_html(md):
    return markdown.markdown(
        md,
        extensions=[
            "extra",
            "sane_lists",
            "smarty",
        ],
        output_format="html5",
    )


def ensure_dir(path):
    path.mkdir(
        parents=True,
        exist_ok=True
    )


def indent_html(
    value,
    spaces
):
    prefix = " " * spaces

    return "\n".join(
        (
            prefix + line
            if line.strip()
            else ""
        )
        for line in value.splitlines()
    )


# =========================================================
# COMMON SITE SHELL
# =========================================================

def site_header(prefix=""):
    return f"""
  <header class="site-header">
    <a href="{prefix}index.html" class="logo">Emma Writes</a>

    <nav class="nav">
      <a href="{prefix}essays.html">Writing</a>
      <a href="{prefix}dayeye.html">Oral History</a>
      <a href="{prefix}work.html">Work Notes</a>
      <a href="{prefix}academic.html">Academic</a>
      <a href="{prefix}index.html#about">About</a>
    </nav>
  </header>
"""


def site_footer(prefix=""):
    return f"""
  <footer>
    <p>© <span id="year"></span> Emma Zhong</p>
    <p class="footer-note">Written slowly. Kept carefully.</p>
  </footer>

  <script src="{prefix}script.js?v=6"></script>
"""


# =========================================================
# ARTICLE PAGES
# =========================================================

def build_writing_article(
    item,
    target_dir
):
    slug = item["_slug"]

    title = str(
        item.get(
            "title",
            slug
        )
    )

    date = display_date(
        item.get(
            "date",
            ""
        )
    )

    category = str(
        item.get(
            "category",
            ""
        )
    )

    category_label = str(
        item.get("category_label")
        or CATEGORY_LABELS.get(
            category,
            category.upper()
            or "WRITING"
        )
    )

    body_html = md_to_html(
        item["_body_markdown"]
    )

    page = f"""<!DOCTYPE html>
<html lang="{html.escape(str(item.get("language", "zh")))}">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>{html.escape(title)} — Emma Writes</title>

  <link rel="stylesheet" href="../style.css?v=10">
</head>

<body>
{site_header("../")}
  <main class="article-page">

    <header class="article-header">
      <p class="article-category">{html.escape(category_label.upper())}</p>

      <h1>{html.escape(title)}</h1>

      <p class="article-date">{html.escape(date)}</p>
    </header>

    <article class="article-body">
{indent_html(body_html, 6)}
    </article>

    <a href="../essays.html" class="back-link">
      ← Back to Writing
    </a>

  </main>
{site_footer("../")}
</body>
</html>
"""

    out = (
        target_dir
        / "essays"
        / f"{slug}.html"
    )

    ensure_dir(
        out.parent
    )

    out.write_text(
        page,
        encoding="utf-8"
    )


def work_label(item):
    series = str(
        item.get(
            "series",
            "Work Log"
        )
    ).strip()

    number = item.get(
        "number",
        ""
    )

    if number == "":
        return series.upper()

    try:
        num_text = (
            f"{int(number):02d}"
        )
    except Exception:
        num_text = str(
            number
        )

    return (
        f"{series.upper()} "
        f"{num_text}"
    )


def build_work_article(
    item,
    target_dir
):
    slug = item["_slug"]

    title = str(
        item.get(
            "title",
            slug
        )
    )

    date = display_date(
        item.get(
            "date",
            ""
        )
    )

    body_html = md_to_html(
        item["_body_markdown"]
    )

    page = f"""<!DOCTYPE html>
<html lang="{html.escape(str(item.get("language", "en")))}">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>{html.escape(title)} — Emma Writes</title>

  <link rel="stylesheet" href="../style.css?v=10">
</head>

<body>
{site_header("../")}
  <main class="article-page">

    <header class="article-header">
      <p class="article-category">{html.escape(work_label(item))}</p>

      <h1>{html.escape(title)}</h1>

      <p class="article-date">{html.escape(date)}</p>
    </header>

    <article class="article-body">
{indent_html(body_html, 6)}
    </article>

    <a href="../work.html" class="back-link">
      ← Back to Work Notes
    </a>

  </main>
{site_footer("../")}
</body>
</html>
"""

    out = (
        target_dir
        / "work"
        / f"{slug}.html"
    )

    ensure_dir(
        out.parent
    )

    out.write_text(
        page,
        encoding="utf-8"
    )


# =========================================================
# WRITING ARCHIVE
# =========================================================

def archive_card(item):
    category = str(
        item.get(
            "category",
            ""
        )
    )

    category_label = str(
        item.get("category_label")
        or CATEGORY_LABELS.get(
            category,
            category
        )
    )

    date = display_date(
        item.get(
            "date",
            ""
        )
    )

    title = str(
        item.get(
            "title",
            "Untitled"
        )
    )

    summary = str(
        item.get(
            "summary",
            ""
        )
    ).strip()

    slug = item["_slug"]

    return f"""
        <a
          href="essays/{html.escape(slug)}.html"
          class="archive-item"
          data-category="{html.escape(category)}"
        >
          <div class="archive-meta">
            <span>{html.escape(category_label)}</span>
            <span>{html.escape(date)}</span>
          </div>

          <div class="archive-title">
            <h2>{html.escape(title)}</h2>
            <p>{html.escape(summary)}</p>
          </div>

          <div class="archive-arrow">→</div>
        </a>
"""


def build_essays_archive(
    items,
    target_dir
):
    cards = "\n".join(
        archive_card(item)
        for item in items
    )

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>Writing — Emma Writes</title>

  <meta
    name="description"
    content="Essays, prose, reading notes, social commentary and poetry by Emma Zhong."
  >

  <link rel="stylesheet" href="style.css?v=10">

  <style>
    .archive-tools {{
      max-width: 1100px;
      margin: 0 auto 54px;
      padding: 0 6vw;
    }}

    .archive-stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 22px;
    }}

    .archive-stat-button {{
      border: 1px solid #d6c5b2;
      background: transparent;
      color: #75685c;
      padding: 8px 12px;
      cursor: pointer;
      font: inherit;
    }}

    .archive-stat-button.active {{
      color: #992f2b;
      border-color: #992f2b;
    }}

    .archive-search-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      max-width: 620px;
    }}

    .archive-search {{
      flex: 1;
      padding: 12px 14px;
      border: 1px solid #d6c5b2;
      background: transparent;
      color: inherit;
      font: inherit;
    }}

    .archive-search-clear {{
      border: 0;
      background: transparent;
      cursor: pointer;
      font: inherit;
      color: #75685c;
    }}

    .archive-search-meta {{
      margin-top: 12px;
      color: #8b796b;
      font-size: 13px;
    }}

    .archive-item.hidden {{
      display: none;
    }}

    .archive-empty {{
      display: none;
      padding: 28px 0;
      color: #75685c;
    }}

    .archive-empty.visible {{
      display: block;
    }}
  </style>
</head>

<body>
{site_header("")}
  <main>

    <section class="archive-hero">
      <p class="eyebrow">WRITING</p>

      <h1>人间书写</h1>

      <p class="archive-intro">
        杂记、散文、读后感、社会评论与诗歌。
        <br>
        写我看见的人，也写我正在经历和思考的世界。
      </p>
    </section>

    <section class="archive-tools">
      <div
        class="archive-stats"
        id="archive-stats"
      ></div>

      <div class="archive-search-row">
        <input
          class="archive-search"
          id="archive-search"
          type="search"
          placeholder="搜索标题或全文…"
          autocomplete="off"
        >

        <button
          class="archive-search-clear"
          id="archive-search-clear"
          type="button"
        >
          Clear
        </button>
      </div>

      <div
        class="archive-search-meta"
        id="archive-search-meta"
      ></div>
    </section>

    <section class="archive-section">
      <div class="archive-list">
{cards}

        <div
          class="archive-empty"
          id="archive-empty"
        >
          没有找到匹配的文章。
        </div>
      </div>
    </section>

  </main>

{site_footer("")}

  <script>
    (() => {{
      const CATEGORY_LABELS = {{
        essay: "杂记",
        prose: "散文",
        reading: "读后感",
        commentary: "社会评论",
        poem: "诗歌"
      }};

      const CATEGORY_ORDER = [
        "essay",
        "prose",
        "reading",
        "commentary",
        "poem"
      ];

      const items = Array.from(
        document.querySelectorAll(
          ".archive-item"
        )
      );

      const stats =
        document.getElementById(
          "archive-stats"
        );

      const input =
        document.getElementById(
          "archive-search"
        );

      const clear =
        document.getElementById(
          "archive-search-clear"
        );

      const meta =
        document.getElementById(
          "archive-search-meta"
        );

      const empty =
        document.getElementById(
          "archive-empty"
        );

      let index = [];
      let activeCategory = "all";
      let query = "";

      function normalize(value) {{
        return String(
          value || ""
        )
          .toLowerCase()
          .normalize("NFKC")
          .replace(/\\s+/g, " ")
          .trim();
      }}

      function renderStats() {{
        const counts = {{}};

        items.forEach(item => {{
          const category =
            item.dataset.category;

          counts[category] =
            (counts[category] || 0)
            + 1;
        }});

        const parts = [
          `<button class="archive-stat-button active" data-category-filter="all" type="button">共 ${{items.length}} 篇</button>`
        ];

        CATEGORY_ORDER.forEach(
          category => {{
            const count =
              counts[category]
              || 0;

            if (count) {{
              parts.push(
                `<button class="archive-stat-button" data-category-filter="${{category}}" type="button">${{CATEGORY_LABELS[category]}} ${{count}}</button>`
              );
            }}
          }}
        );

        stats.innerHTML =
          parts.join("");

        stats
          .querySelectorAll(
            ".archive-stat-button"
          )
          .forEach(button => {{
            button.addEventListener(
              "click",
              () => {{
                activeCategory =
                  button.dataset
                    .categoryFilter;

                stats
                  .querySelectorAll(
                    ".archive-stat-button"
                  )
                  .forEach(b => {{
                    b.classList.toggle(
                      "active",
                      b.dataset
                        .categoryFilter
                        === activeCategory
                    );
                  }});

                apply();
              }}
            );
          }});
      }}

      function recordFor(item) {{
        const href =
          item.getAttribute(
            "href"
          );

        return index.find(
          record =>
            record.href === href
        );
      }}

      function apply() {{
        let visible = 0;

        items.forEach(item => {{
          const categoryMatch =
            activeCategory === "all"
            ||
            item.dataset.category
              === activeCategory;

          let searchMatch = true;

          if (query) {{
            const record =
              recordFor(item);

            if (record) {{
              searchMatch =
                record.search
                  .includes(query);
            }} else {{
              searchMatch =
                normalize(
                  item.textContent
                ).includes(query);
            }}
          }}

          const show =
            categoryMatch
            &&
            searchMatch;

          item.classList.toggle(
            "hidden",
            !show
          );

          if (show) {{
            visible += 1;
          }}
        }});

        empty.classList.toggle(
          "visible",
          visible === 0
        );

        if (query) {{
          meta.textContent =
            `找到 ${{visible}} 篇`;
        }} else {{
          meta.textContent =
            `全文索引：${{index.length}} 篇`;
        }}
      }}

      input.addEventListener(
        "input",
        () => {{
          query = normalize(
            input.value
          );

          apply();
        }}
      );

      clear.addEventListener(
        "click",
        () => {{
          input.value = "";
          query = "";
          input.focus();
          apply();
        }}
      );

      renderStats();

      fetch(
        "search-index.json",
        {{
          cache: "no-cache"
        }}
      )
        .then(response => {{
          if (!response.ok) {{
            throw new Error(
              "Could not load search-index.json"
            );
          }}

          return response.json();
        }})
        .then(data => {{
          index = data.map(
            record => ({{
              ...record,
              search: normalize(
                `${{record.title || ""}} ${{record.content || ""}}`
              )
            }})
          );

          apply();
        }})
        .catch(error => {{
          console.error(error);

          meta.textContent =
            "全文索引加载失败。";

          apply();
        }});
    }})();
  </script>

</body>
</html>
"""

    (
        target_dir
        / "essays.html"
    ).write_text(
        page,
        encoding="utf-8"
    )


# =========================================================
# WORK ARCHIVE
# =========================================================

def work_card(item):
    title = str(
        item.get(
            "title",
            "Untitled"
        )
    )

    date = display_date(
        item.get(
            "date",
            ""
        )
    )

    summary = str(
        item.get(
            "summary",
            ""
        )
    ).strip()

    body_plain = strip_markdown(
        item["_body_markdown"]
    )

    if not summary:
        summary = body_plain[:180]

        if len(body_plain) > 180:
            summary += "…"

    slug = item["_slug"]

    return f"""
        <a
          href="work/{html.escape(slug)}.html"
          class="archive-item"
        >
          <div class="archive-meta">
            <span>{html.escape(work_label(item))}</span>
            <span>{html.escape(date)}</span>
          </div>

          <div class="archive-title">
            <h2>{html.escape(title)}</h2>
            <p>{html.escape(summary)}</p>
          </div>

          <div class="archive-arrow">→</div>
        </a>
"""


def build_work_archive(
    items,
    target_dir
):
    cards = "\n".join(
        work_card(item)
        for item in items
    )

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>Work Notes — Emma Writes</title>

  <meta
    name="description"
    content="Work observations by Emma Zhong."
  >

  <link rel="stylesheet" href="style.css?v=10">
</head>

<body>
{site_header("")}
  <main>

    <section class="archive-hero">
      <p class="eyebrow">WORK NOTES</p>

      <h1>工作手记</h1>

      <p class="archive-intro">
        关于教育、学生、产品、传播与日常工作的记录。
        <br>
        有些问题，只有真正做起来之后才会出现。
      </p>
    </section>

    <section class="archive-section">
      <div class="archive-list">
{cards}
      </div>
    </section>

  </main>
{site_footer("")}
</body>
</html>
"""

    (
        target_dir
        / "work.html"
    ).write_text(
        page,
        encoding="utf-8"
    )


# =========================================================
# SEARCH INDEX
# =========================================================

def build_search_index(
    items,
    target_dir
):
    records = []

    for item in items:
        records.append({
            "href":
                f"essays/{item['_slug']}.html",
            "title":
                str(
                    item.get(
                        "title",
                        ""
                    )
                ),
            "content":
                strip_markdown(
                    item["_body_markdown"]
                ),
        })

    (
        target_dir
        / "search-index.json"
    ).write_text(
        json.dumps(
            records,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


# =========================================================
# PREVIEW COPY
# =========================================================

def copy_shared_files_for_preview():
    for name in [
        "style.css",
        "home-v1.css",
        "script.js",
        "index.html",
        "dayeye.html",
        "academic.html",
    ]:
        src = ROOT / name

        if src.exists():
            shutil.copy2(
                src,
                PREVIEW_DIR / name
            )

    for dirname in [
        "images",
        "dayeye",
    ]:
        src = ROOT / dirname
        dst = (
            PREVIEW_DIR
            / dirname
        )

        if src.exists():
            shutil.copytree(
                src,
                dst,
                dirs_exist_ok=True
            )


# =========================================================
# LOAD CONTENT
# =========================================================

def load_public_content(folder):
    if not folder.exists():
        return []

    items = []

    for path in sorted(
        folder.glob("*.md")
    ):
        item = read_markdown_file(
            path
        )

        if (
            item.get(
                "visibility",
                "public"
            )
            != "public"
        ):
            continue

        items.append(
            item
        )

    items.sort(
        key=lambda item:
            date_sort_key(
                item.get(
                    "date",
                    ""
                )
            ),
        reverse=True
    )

    return items


# =========================================================
# BUILD
# =========================================================

def build(target_dir):
    ensure_dir(
        target_dir
    )

    writing = load_public_content(
        WRITING_DIR
    )

    work = load_public_content(
        WORK_DIR
    )

    print(
        f"Writing Markdown files: "
        f"{len(writing)}"
    )

    print(
        f"Work Markdown files: "
        f"{len(work)}"
    )

    for item in writing:
        build_writing_article(
            item,
            target_dir
        )

    for item in work:
        build_work_article(
            item,
            target_dir
        )

    build_essays_archive(
        writing,
        target_dir
    )

    build_work_archive(
        work,
        target_dir
    )

    build_search_index(
        writing,
        target_dir
    )


def preview():
    if PREVIEW_DIR.exists():
        shutil.rmtree(
            PREVIEW_DIR
        )

    ensure_dir(
        PREVIEW_DIR
    )

    build(
        PREVIEW_DIR
    )

    copy_shared_files_for_preview()

    print()
    print(
        "Preview build complete."
    )

    print(
        f"Output: {PREVIEW_DIR}"
    )

    print()
    print(
        "Nothing in the live site "
        "was overwritten."
    )

    print()
    print("To preview:")
    print(
        "  cd _site_preview"
    )
    print(
        "  python3 -m http.server 8000"
    )


def publish():
    print(
        "Publishing generated pages "
        "into the live repository..."
    )

    build(
        ROOT
    )

    print()
    print(
        "Publish build complete."
    )

    print()
    print(
        "Generated/updated:"
    )
    print(
        "  essays.html"
    )
    print(
        "  work.html"
    )
    print(
        "  search-index.json"
    )
    print(
        "  essays/*.html"
    )
    print(
        "  work/*.html"
    )

    print()
    print(
        "Not touched:"
    )
    print(
        "  index.html"
    )
    print(
        "  style.css"
    )
    print(
        "  script.js"
    )
    print(
        "  dayeye.html / dayeye/"
    )
    print(
        "  academic.html"
    )
    print(
        "  images/"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Build Emma Writes "
            "from Markdown source files."
        )
    )

    parser.add_argument(
        "--publish",
        action="store_true",
        help=(
            "Write generated files "
            "into the live repository. "
            "Without this flag, a safe "
            "_site_preview build is created."
        )
    )

    args = parser.parse_args()

    if args.publish:
        publish()
    else:
        preview()


if __name__ == "__main__":
    main()
