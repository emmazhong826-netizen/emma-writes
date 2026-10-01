from pathlib import Path
from html.parser import HTMLParser
import html
import re


ROOT = Path(__file__).resolve().parent.parent

ESSAYS_DIR = ROOT / "essays"
ARCHIVE_FILE = ROOT / "essays.html"
OUTPUT_DIR = ROOT / "content" / "writing"


CATEGORY_NAMES = {
    "essay": "杂记",
    "prose": "散文",
    "reading": "读后感",
    "commentary": "社会评论",
    "poem": "诗歌",
}


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_html_text(value):

    value = re.sub(
        r"<[^>]+>",
        "",
        value
    )

    value = html.unescape(value)

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def yaml_string(value):

    value = str(
        value or ""
    )

    value = value.replace(
        "\\",
        "\\\\"
    )

    value = value.replace(
        '"',
        '\\"'
    )

    return f'"{value}"'


def detect_language(text):

    chinese_chars = len(
        re.findall(
            r"[\u4e00-\u9fff]",
            text
        )
    )

    english_letters = len(
        re.findall(
            r"[A-Za-z]",
            text
        )
    )

    if chinese_chars > english_letters / 3:
        return "zh"

    return "en"


# =========================================================
# ARCHIVE METADATA
# =========================================================

def read_archive_metadata():

    source = ARCHIVE_FILE.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    metadata = {}

    pattern = re.compile(
        r"""
        <a
        [^>]*?
        href=["'](?P<href>essays/[^"']+\.html)["']
        [^>]*?
        class=["'][^"']*archive-item[^"']*["']
        [^>]*?
        data-category=["'](?P<category>[^"']+)["']
        [^>]*?
        >
        (?P<body>.*?)
        </a>
        """,
        re.S | re.X | re.I
    )

    for match in pattern.finditer(source):

        href = match.group("href")
        category = match.group("category")
        body = match.group("body")


        spans = re.findall(
            r"<span[^>]*>(.*?)</span>",
            body,
            re.S | re.I
        )

        spans = [
            clean_html_text(item)
            for item in spans
        ]


        title_match = re.search(
            r"<h2[^>]*>(.*?)</h2>",
            body,
            re.S | re.I
        )


        summary_match = re.search(
            r"""<div
                [^>]*
                class=["'][^"']*archive-title[^"']*["']
                [^>]*
                >
                .*?
                <p[^>]*>(.*?)</p>
            """,
            body,
            re.S | re.I | re.X
        )


        title = ""

        if title_match:
            title = clean_html_text(
                title_match.group(1)
            )


        summary = ""

        if summary_match:
            summary = clean_html_text(
                summary_match.group(1)
            )


        date = ""

        if len(spans) >= 2:
            date = spans[1]


        filename = Path(
            href
        ).name


        metadata[filename] = {
            "href": href,
            "category": category,
            "category_name":
                CATEGORY_NAMES.get(
                    category,
                    category
                ),
            "title": title,
            "date": date,
            "summary": summary,
        }


    return metadata


# =========================================================
# GET ONLY THE WRITING BODY
# =========================================================

def extract_content_fragment(source):

    # -----------------------------------------------------
    # 1. Preferred modern structure
    # -----------------------------------------------------

    match = re.search(
        r"""
        <article
        [^>]*
        class=["'][^"']*article-body[^"']*["']
        [^>]*
        >
        (?P<body>.*?)
        </article>
        """,
        source,
        re.S | re.I | re.X
    )

    if match:
        return match.group("body")


    # -----------------------------------------------------
    # 2. Older pages using plain <article>
    # -----------------------------------------------------

    match = re.search(
        r"""
        <article
        [^>]*
        >
        (?P<body>.*?)
        </article>
        """,
        source,
        re.S | re.I | re.X
    )

    if match:
        return match.group("body")


    # -----------------------------------------------------
    # 3. Oldest fallback: <main>
    # -----------------------------------------------------

    match = re.search(
        r"""
        <main
        [^>]*
        >
        (?P<body>.*?)
        </main>
        """,
        source,
        re.S | re.I | re.X
    )

    if match:

        body = match.group(
            "body"
        )

        # Remove article header if present.
        body = re.sub(
            r"""
            <header
            [^>]*
            class=["'][^"']*article-header[^"']*["']
            [^>]*
            >
            .*?
            </header>
            """,
            "",
            body,
            flags=re.S | re.I | re.X
        )


        # Remove Back to Writing / other navigation links.
        body = re.sub(
            r"""
            <a
            [^>]*
            class=["'][^"']*back-link[^"']*["']
            [^>]*
            >
            .*?
            </a>
            """,
            "",
            body,
            flags=re.S | re.I | re.X
        )


        return body


    return ""


# =========================================================
# HTML FRAGMENT → MARKDOWN
# =========================================================

class FragmentToMarkdown(HTMLParser):

    def __init__(self):

        super().__init__()

        self.output = []

        self.link_stack = []

        self.skip_depth = 0


    def handle_starttag(
        self,
        tag,
        attrs
    ):

        tag = tag.lower()

        attrs_dict = dict(
            attrs
        )


        if tag in [
            "script",
            "style",
            "nav",
            "footer"
        ]:

            self.skip_depth += 1

            return


        if self.skip_depth:
            return


        if tag == "p":

            self.blank_line()


        elif tag == "h1":

            self.blank_line()

            self.output.append(
                "# "
            )


        elif tag == "h2":

            self.blank_line()

            self.output.append(
                "## "
            )


        elif tag == "h3":

            self.blank_line()

            self.output.append(
                "### "
            )


        elif tag == "blockquote":

            self.blank_line()

            self.output.append(
                "> "
            )


        elif tag == "br":

            self.output.append(
                "  \n"
            )


        elif tag in [
            "em",
            "i"
        ]:

            self.output.append(
                "*"
            )


        elif tag in [
            "strong",
            "b"
        ]:

            self.output.append(
                "**"
            )


        elif tag == "li":

            self.line_start()

            self.output.append(
                "- "
            )


        elif tag == "a":

            href = attrs_dict.get(
                "href",
                ""
            )

            self.output.append(
                "["
            )

            self.link_stack.append(
                href
            )


    def handle_endtag(
        self,
        tag
    ):

        tag = tag.lower()


        if tag in [
            "script",
            "style",
            "nav",
            "footer"
        ]:

            if self.skip_depth:
                self.skip_depth -= 1

            return


        if self.skip_depth:
            return


        if tag in [
            "p",
            "h1",
            "h2",
            "h3",
            "blockquote",
            "li"
        ]:

            self.output.append(
                "\n\n"
            )


        elif tag in [
            "em",
            "i"
        ]:

            self.output.append(
                "*"
            )


        elif tag in [
            "strong",
            "b"
        ]:

            self.output.append(
                "**"
            )


        elif tag == "a":

            href = ""

            if self.link_stack:
                href = self.link_stack.pop()

            self.output.append(
                f"]({href})"
            )


    def handle_data(
        self,
        data
    ):

        if self.skip_depth:
            return

        self.output.append(
            html.unescape(data)
        )


    def blank_line(self):

        current = "".join(
            self.output
        )

        if (
            current
            and not current.endswith(
                "\n\n"
            )
        ):

            self.output.append(
                "\n\n"
            )


    def line_start(self):

        current = "".join(
            self.output
        )

        if (
            current
            and not current.endswith(
                "\n"
            )
        ):

            self.output.append(
                "\n"
            )


    def markdown(self):

        text = "".join(
            self.output
        )


        text = re.sub(
            r"[ \t]+\n",
            "\n",
            text
        )


        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )


        return text.strip()


# =========================================================
# CONVERT ONE HTML FILE
# =========================================================

def convert_article(file_path):

    source = file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )


    fragment = extract_content_fragment(
        source
    )


    if not fragment:
        return ""


    parser = FragmentToMarkdown()

    parser.feed(
        fragment
    )


    return parser.markdown()


# =========================================================
# TITLE FALLBACK
# =========================================================

def get_html_title(file_path):

    source = file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )


    match = re.search(
        r"<title[^>]*>(.*?)</title>",
        source,
        re.S | re.I
    )


    if not match:
        return ""


    title = clean_html_text(
        match.group(1)
    )


    title = re.sub(
        r"\s*[—\-]\s*Emma Writes\s*$",
        "",
        title,
        flags=re.I
    )


    return title.strip()


# =========================================================
# MIGRATION
# =========================================================

def migrate():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    metadata = (
        read_archive_metadata()
    )


    files = sorted(
        ESSAYS_DIR.glob(
            "*.html"
        )
    )


    converted = 0
    skipped = 0


    for file_path in files:

        slug = file_path.stem


        output_path = (
            OUTPUT_DIR
            /
            f"{slug}.md"
        )


        if output_path.exists():

            print(
                f"EXISTS: {output_path.name}"
            )

            skipped += 1

            continue


        body = convert_article(
            file_path
        )


        if not body:

            print(
                f"SKIPPED: {file_path.name} "
                "(no readable writing body)"
            )

            skipped += 1

            continue


        info = metadata.get(
            file_path.name,
            {}
        )


        title = info.get(
            "title",
            ""
        )


        if not title:

            title = get_html_title(
                file_path
            )


        date = info.get(
            "date",
            ""
        )


        category = info.get(
            "category",
            ""
        )


        category_name = info.get(
            "category_name",
            ""
        )


        summary = info.get(
            "summary",
            ""
        )


        language = detect_language(
            body
        )


        permanent_id = (
            "EW-WRITING-"
            +
            slug.upper().replace(
                "-",
                "_"
            )
        )


        frontmatter = [
            "---",
            f"id: {yaml_string(permanent_id)}",
            f"title: {yaml_string(title)}",
            f"date: {yaml_string(date)}",
            "section: writing",
            f"category: {yaml_string(category)}",
            f"category_label: {yaml_string(category_name)}",
            "visibility: public",
            f"language: {language}",
            f"slug: {yaml_string(slug)}",
            f"summary: {yaml_string(summary)}",
            f"legacy_html: {yaml_string('essays/' + file_path.name)}",
            "---",
            "",
        ]


        output = (
            "\n".join(
                frontmatter
            )
            +
            body
            +
            "\n"
        )


        output_path.write_text(
            output,
            encoding="utf-8"
        )


        converted += 1


        print(
            f"CREATED: {output_path.name}"
        )


    print()

    print(
        "Migration finished."
    )

    print(
        f"{converted} Markdown files created."
    )

    print(
        f"{skipped} skipped."
    )

    print()

    print(
        "Existing website HTML was not modified."
    )


if __name__ == "__main__":

    migrate()