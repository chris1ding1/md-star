"""
A Python static site generator that converts Markdown files to HTML websites.
"""

import json
import shutil
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree as ET

import frontmatter
import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from slugify import slugify


class MarkdownSiteGenerator:
    """
    Core class for static site generation.
    Handles Markdown conversion, template rendering, and static file generation.
    """

    X_CARD_TYPE_SUMMARY = "summary"

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the static site generator."""

        self.config_path = Path(config_path).absolute()
        self.project_dir = self.config_path.parent

        # Load and parse the YAML site configuration file
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # Setup Jinja2 template environment
        templates_dir = self.project_dir / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir)), autoescape=select_autoescape()
        )

        # Setup Markdown converter
        self.md = markdown.Markdown(extensions=["fenced_code", "tables", "def_list"])

    def run(self):
        """Entry point for static site generation."""

        content_dir = Path(self.config["paths"]["content"])
        output_dir = Path(self.config["paths"]["output"])
        drafts_dir = content_dir / self.config["paths"]["drafts"]

        # Clean and create output directory
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)

        # Create posts directory
        posts_dir = output_dir / "posts"
        posts_dir.mkdir(exist_ok=True)

        # Process all posts
        posts = []
        for md_file in content_dir.rglob("*.md"):
            # Skip draft files
            if drafts_dir in md_file.parents:  #
                print(f"Skipping draft: {md_file.relative_to(content_dir)}")
                continue

            # Process post data.
            post_data = self.build_post_data(md_file)
            posts.append(post_data)

            # Render post page
            template = self.jinja_env.get_template("post.html")
            html = template.render(
                site={
                    **self.config["site"],
                },
                page={
                    "lang": post_data["lang"],
                    "description": post_data["description"],
                    "keywords": post_data["keywords"],
                    "title": post_data["title"],
                },
                post=post_data,
                x_card_html=post_data["x_card_html"],
                canonical_link_html=post_data["canonical_link_html"],
            )

            # Save post page
            output_file = output_dir / post_data["file_path"].lstrip("/")
            output_file.parent.mkdir(exist_ok=True)
            output_file.write_text(html, encoding="utf-8")

        # Generate index page
        self.generate_index(posts, output_dir)

        # Generate about page
        self.generate_about(output_dir)

        # Generate sitemap
        self.generate_sitemap(posts, output_dir)

        # Copy static files
        self.copy_public_files()

        print(f"Site generation completed! Processed {len(posts)} posts.")

    def build_post_data(self, file_path: Path) -> dict:
        """Build a post data dictionary from a Markdown file."""

        # Get language
        file_stem = file_path.stem
        lang_parts = file_stem.split(".")
        lang = (
            lang_parts[-1]
            if len(lang_parts) > 1
            else self.config["site"].get("locale", "en")
        )

        # Load post.md content
        post = frontmatter.load(str(file_path), disable_yaml_loader=True)

        # Convert markdown to html
        html_content = self.md.convert(post.content)

        # Get title
        title = post.metadata.get("title", "Untitled")

        # Slug
        slug_source = None
        if post.metadata.get("slug") and post.metadata["slug"].strip():
            slug_source = post.metadata["slug"]
        elif post.metadata.get("title") and post.metadata["title"].strip():
            slug_source = post.metadata["title"]
        else:
            slug_source = self.config["name"].get("name", "untitled")
        slug = slugify(slug_source)

        schema_article = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": title,
        }

        author = []
        if self.config["site"].get("author", ""):
            author.append({"@type": "Person", "name": self.config["site"]["author"]})

        if author:
            schema_article["author"] = author

        path = f"/posts/{slug}"
        return {
            "content": html_content,
            "title": title,
            "created": post.metadata.get("created", ""),
            "updated": post.metadata.get("updated", ""),
            "url": path,
            "file_path": f"{path}.html",
            "lang": lang,
            "description": post.metadata.get("description", ""),
            "keywords": post.metadata.get("keywords", []),
            "schema_article": json.dumps(schema_article, ensure_ascii=False),
            "x_card_html": self.generate_x_card(
                card_type=self.X_CARD_TYPE_SUMMARY,
                title=title,
                description=post.metadata.get("description", ""),
            ),
            "canonical_link_html": self.generate_canonical_link(
                path=path,
            ),
        }

    def generate_index(self, posts: list, output_dir: Path):
        """Generate index page"""
        sorted_posts = posts

        sort_by = self.config["site"].get("sort_by")
        if sort_by:
            sorted_posts = sorted(
                posts,
                key=lambda x: str(x.get(sort_by)) if x.get(sort_by) is not None else "",
                reverse=True,
            )

        template = self.jinja_env.get_template("index.html")
        html = template.render(
            site={**self.config["site"]},
            posts=sorted_posts,
            schema_site_name=self.generate_schema_site_name(),
            x_card_html=self.generate_x_card(
                card_type=self.X_CARD_TYPE_SUMMARY,
                title=self.config["site"]["name"],
                description=self.config["site"]["description"],
            ),
            canonical_link_html=self.generate_canonical_link(
                path="/",
            ),
        )

        output_file = output_dir / "index.html"
        output_file.write_text(html, encoding="utf-8")

    def generate_about(self, output_dir: Path):
        """Generate about page"""

        template = self.jinja_env.get_template("about.html")
        html = template.render(
            site={**self.config["site"]},
            page={
                "title": "About",
                "description": "About me",
                "keywords": ["About", "Bio"],
            },
            projects=self.config.get("projects", []),
            x_card_html=self.generate_x_card(
                card_type=self.X_CARD_TYPE_SUMMARY,
                title="About",
                description="About me",
            ),
            canonical_link_html=self.generate_canonical_link(
                path="/about",
            ),
        )

        output_file = output_dir / "about.html"
        output_file.write_text(html, encoding="utf-8")

    def generate_sitemap(self, posts: list, output_dir: Path):
        """Generate sitemap"""

        # Create root element, add namespace
        urlset = ET.Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

        # Add home page
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = self.config["site"]["url"]

        # Add all posts
        for post in posts:
            url = ET.SubElement(urlset, "url")
            loc = ET.SubElement(url, "loc")
            loc.text = self.config["site"]["url"] + post["url"]
            # last modified
            if post["updated"]:
                lastmod = ET.SubElement(url, "lastmod")
                lastmod.text = post["updated"].strftime("%Y-%m-%d")
            elif post["created"]:
                lastmod = ET.SubElement(url, "lastmod")
                lastmod.text = post["created"].strftime("%Y-%m-%d")

        # Add about page
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = self.config["site"]["url"] + "/about"

        # Write to file, add XML declaration and correct indentation
        output_file = output_dir / "sitemap.xml"
        xml_str = minidom.parseString(
            ET.tostring(urlset, encoding="utf-8")
        ).toprettyxml(indent="  ", encoding="utf-8")
        output_file.write_bytes(xml_str)

    def generate_schema_site_name(self):
        """Generate schema site name"""
        site_name = self.config["site"].get("name").strip()
        site_url = self.config["site"].get("url").strip()

        if site_name and site_url:
            schema_site_name = {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": site_name,
            }
            site_alternate_name = self.config["site"].get("alternate_name")
            if site_alternate_name:
                schema_site_name["alternateName"] = site_alternate_name
            schema_site_name["url"] = site_url.rstrip("/") + "/"
            return json.dumps(schema_site_name, ensure_ascii=False)
        return None

    def generate_x_card(self, card_type, title, description):
        """Generate X card"""
        processed_title = title
        if len(title) > 70:
            processed_title = title[:67] + "..."

        processed_description = description
        if len(description) > 200:
            processed_description = description[:197] + "..."

        x_account = self.config["site"]["socials"].get("x", "")
        template = self.jinja_env.get_template("components/x_card.html")
        html = template.render(
            x_card={
                "card_type": card_type,
                "site": x_account,
                "title": processed_title,
                "description": processed_description,
            }
        )
        return html

    def generate_canonical_link(self, path: str) -> str:
        """Generate canonical link"""
        site_url = self.config["site"].get("url", "")
        if not site_url:
            return ""

        url = site_url.rstrip("/") + "/" + path.lstrip("/")
        return f'<link rel="canonical" href="{url}">'

    def copy_public_files(self):
        """Copy static files"""

        def ignore_files(_, names):
            return [
                n
                for n in names
                if n.startswith(".DS_Store") or n.endswith((".swp", ".swo"))
            ]

        public_dir = self.project_dir / self.config["paths"]["public"]
        output_dir = self.project_dir / self.config["paths"]["output"]

        shutil.copytree(public_dir, output_dir, dirs_exist_ok=True, ignore=ignore_files)


if __name__ == "__main__":
    MarkdownSiteGenerator().run()
