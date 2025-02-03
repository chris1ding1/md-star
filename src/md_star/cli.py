import os
import shutil
from pathlib import Path

import click

from md_star.generator import MarkdownSiteGenerator


@click.group()
def cli():
    """MD-Star: A Markdown Static Site Generator"""
    pass


@cli.command()
@click.argument("project_dir", default=".")
def init(project_dir: str):
    """Initialize a new MD-Star project"""
    project_path = Path(project_dir).absolute()
    package_dir = Path(__file__).parent

    # 创建基本目录
    dirs = ["content", "content/drafts", "templates", "public"]
    for dir_name in dirs:
        dir_path = project_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            click.echo(f"Created directory: {dir_path}")

    # 复制源码目录下的文件
    for src_dir in ["templates", "public", "content"]:
        src_path = package_dir / src_dir
        if src_path.exists():
            for src_file in src_path.rglob("*"):
                if src_file.is_file():
                    relative_path = src_file.relative_to(src_path)
                    dst_file = project_path / src_dir / relative_path
                    if not dst_file.exists():
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        click.echo(f"Copied {src_dir} file: {relative_path}")

    # 复制配置文件
    config_src = package_dir / "config.yaml"
    config_dst = project_path / "config.yaml"
    if config_src.exists() and not config_dst.exists():
        shutil.copy2(config_src, config_dst)
        click.echo("Copied config.yaml")

    click.echo(f"✨ Project initialized in {project_path}")

    # 自动构建
    if click.confirm("Would you like to build the site now?"):
        generator = MarkdownSiteGenerator(str(config_dst))
        generator.run()
        click.echo("🎉 Site built successfully!")


@cli.command()
def build():
    """Build static site from markdown files"""
    try:
        generator = MarkdownSiteGenerator("config.yaml")
        generator.run()
        click.echo("🎉 Site built successfully!")
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


def main():
    cli()


if __name__ == "__main__":
    main()
