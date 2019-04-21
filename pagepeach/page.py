import jinja2
import os
import markdown
from pathlib import Path

import utils


class Page:
    def __init__(self, config, markdown_path):
        self.config = config
        self.markdown_path = markdown_path

    def read(self):
        with open(self.markdown_path, "r") as f:
            return f.read()

    def generate_html(self, sitemap):
        template_path = Path(os.path.realpath(__file__)).parent / "template"

        template_loader = jinja2.FileSystemLoader(searchpath=str(template_path))
        template_env = jinja2.Environment(loader=template_loader)
        template_env.globals.update(get_url=utils.get_url)

        template = template_env.get_template("index.html")

        return template.render(config=self.config, sitemap=sitemap, title=self.title(), content=self.content())

    def title(self):
        with open(self.markdown_path, "r") as f:
            first_line = f.readline()

        if first_line.startswith("# "):
            return first_line.lstrip("#").strip(" ")
        else:
            return self.markdown_path.name \
                .replace(".md", "") \
                .replace("-", " ") \
                .title()

    def content(self):
        with open(self.markdown_path, "r") as f:
            return markdown.markdown(f.read(), extensions=["fenced_code"])

    def get_path(self):
        return str(self.markdown_path).replace("docs/", "").replace(".md", "")

    def save_html(self, dist_path, sitemap):
        html_path = Path(dist_path / (self.get_path() + ".html"))

        if "/" in self.get_path():
            folder = html_path.parent
            folder.mkdir(exist_ok=True)

        with open(html_path, "w") as f:
            f.write(self.generate_html(sitemap))

    def to_nav_dict(self, current_page):
        active = False
        if not isinstance(current_page, Section):
            active = current_page.markdown_path == self.markdown_path

        return {
            "type": "page",
            "title": self.title(),
            "path": self.get_path() + ".html",
            "active": active
        }


class Section:
    def __init__(self, config, folder_path):
        self.config = config
        self.folder_path = folder_path
        self.children = self.get_children()

    def get_children(self):
        children = []

        for child in self.folder_path.iterdir():
            if child.suffix != ".md":
                continue
            page = Page(self.config, child)
            children.append(page)

        return children

    def title(self):
        return self.folder_path.name \
            .replace("-", " ") \
            .upper()

    def save_html(self, dist_path, sitemap):
        for child in self.children:
            child.save_html(dist_path, sitemap)

    def to_nav_dict(self, current_page):
        return {
            "type": "section",
            "title": self.title(),
            "children": [p.to_nav_dict(p) for p in self.children]
        }
