from pathlib import Path
from html.parser import HTMLParser
import html
import json
import re


ROOT = Path(__file__).resolve().parent
ESSAYS_DIR = ROOT / "essays"
OUTPUT_FILE = ROOT / "search-index.json"


class ArticleParser(HTMLParser):

    def __init__(self):
        super().__init__()

        self.in_title = False

        self.in_article_body = False
        self.article_body_depth = 0

        self.in_article = False
        self.article_depth = 0

        self.in_main = False
        self.main_depth = 0

        self.title_parts = []
        self.article_body_parts = []
        self.article_parts = []
        self.main_parts = []

        self.skip_depth = 0


    def handle_starttag(self, tag, attrs):

        attrs_dict = dict(attrs)
        class_names = attrs_dict.get("class", "").split()

        # -----------------------------------------
        # Ignore script/style/nav/footer
        # -----------------------------------------

        if tag in ["script", "style", "nav", "footer"]:
            self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return


        # -----------------------------------------
        # TITLE
        # -----------------------------------------

        if tag == "title":
            self.in_title = True


        # -----------------------------------------
        # Preferred: .article-body
        # -----------------------------------------

        if tag == "article" and "article-body" in class_names:
            self.in_article_body = True
            self.article_body_depth = 1
            return

        if self.in_article_body:
            self.article_body_depth += 1

            if tag in [
                "p",
                "h1",
                "h2",
                "h3",
                "blockquote",
                "li",
                "br"
            ]:
                self.article_body_parts.append(" ")


        # -----------------------------------------
        # Fallback: any <article>
        # -----------------------------------------

        if tag == "article":
            self.in_article = True
            self.article_depth = 1
            return

        if self.in_article:
            self.article_depth += 1

            if tag in [
                "p",
                "h1",
                "h2",
                "h3",
                "blockquote",
                "li",
                "br"
            ]:
                self.article_parts.append(" ")


        # -----------------------------------------
        # Final fallback: <main>
        # -----------------------------------------

        if tag == "main":
            self.in_main = True
            self.main_depth = 1
            return

        if self.in_main:
            self.main_depth += 1

            if tag in [
                "p",
                "h1",
                "h2",
                "h3",
                "blockquote",
                "li",
                "br"
            ]:
                self.main_parts.append(" ")


    def handle_endtag(self, tag):

        if tag in ["script", "style", "nav", "footer"]:
            if self.skip_depth > 0:
                self.skip_depth -= 1
            return

        if self.skip_depth > 0:
            return


        if tag == "title":
            self.in_title = False


        if self.in_article_body:

            self.article_body_depth -= 1

            if tag in [
                "p",
                "h1",
                "h2",
                "h3",
                "blockquote",
                "li"
            ]:
                self.article_body_parts.append(" ")

            if self.article_body_depth == 0:
                self.in_article_body = False


        if self.in_article:

            self.article_depth -= 1

            if tag in [
                "p",
                "h1",
                "h2",
                "h3",
                "blockquote",
                "li"
            ]:
                self.article_parts.append(" ")

            if self.article_depth == 0:
                self.in_article = False


        if self.in_main:

            self.main_depth -= 1

            if tag in [
                "p",
                "h1",
                "h2",
                "h3",
                "blockquote",
                "li"
            ]:
                self.main_parts.append(" ")

            if self.main_depth == 0:
                self.in_main = False


    def handle_data(self, data):

        if self.skip_depth > 0:
            return


        if self.in_title:
            self.title_parts.append(data)


        if self.in_article_body:
            self.article_body_parts.append(data)


        if self.in_article:
            self.article_parts.append(data)


        if self.in_main:
            self.main_parts.append(data)


    def clean_text(self, parts):

        text = "".join(parts)

        text = html.unescape(text)

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()


    def get_title(self):

        title = self.clean_text(
            self.title_parts
        )

        title = re.sub(
            r"\s*[—\-]\s*Emma Writes\s*$",
            "",
            title,
            flags=re.IGNORECASE
        )

        return title.strip()


    def get_body(self):

        # 1. Best structure
        body = self.clean_text(
            self.article_body_parts
        )

        if body:
            return body


        # 2. Older article pages
        body = self.clean_text(
            self.article_parts
        )

        if body:
            return body


        # 3. Last fallback
        body = self.clean_text(
            self.main_parts
        )

        return body


def read_article(file_path):

    try:

        text = file_path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        text = file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )


    parser = ArticleParser()

    parser.feed(text)


    title = parser.get_title()

    body = parser.get_body()


    return title, body


def build_index():

    if not ESSAYS_DIR.exists():

        print(
            "ERROR: essays/ folder does not exist."
        )

        return


    files = sorted(
        ESSAYS_DIR.glob("*.html")
    )


    search_index = []


    indexed = 0
    skipped = 0


    for file_path in files:

        title, body = read_article(
            file_path
        )


        if not body:

            print(
                f"SKIPPED: {file_path.name} "
                "(no readable article content found)"
            )

            skipped += 1

            continue


        search_index.append({

            "href":
                f"essays/{file_path.name}",

            "title":
                title,

            "content":
                body

        })


        indexed += 1


        print(
            f"INDEXED: {file_path.name}"
        )


    OUTPUT_FILE.write_text(

        json.dumps(
            search_index,
            ensure_ascii=False,
            indent=2
        ),

        encoding="utf-8"
    )


    print()

    print("Finished.")

    print(
        f"{indexed} articles indexed."
    )

    print(
        f"{skipped} articles skipped."
    )

    print(
        f"Created: {OUTPUT_FILE.name}"
    )


if __name__ == "__main__":

    build_index()