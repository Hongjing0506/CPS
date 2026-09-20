#!/usr/bin/env python3
"""Compile the cover and prepend it to the Obsidian-rendered body PDF."""

from argparse import ArgumentParser
from pathlib import Path
import shutil
import subprocess
import tempfile


SOURCE_DIR = Path(__file__).resolve().parent
DOCS_DIR = SOURCE_DIR.parent
COVER_SOURCE = SOURCE_DIR / "CPS_user_manual_cover.tex"
BODY_PDF = SOURCE_DIR / "正文.pdf"
DEFAULT_OUTPUT = DOCS_DIR / "社区区域气候模式预处理系统用户手册.pdf"


def require_file(path):
    if not path.is_file():
        raise SystemExit(f"找不到输入文件：{path}")


def require_executable(name):
    executable = shutil.which(name)
    if executable is None:
        raise SystemExit(f"找不到可执行程序：{name}")
    return executable


def render_cover(xelatex, build_dir):
    command = [
        xelatex,
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={build_dir}",
        str(COVER_SOURCE),
    ]
    subprocess.run(command, cwd=SOURCE_DIR, check=True)
    return build_dir / f"{COVER_SOURCE.stem}.pdf"


def merge_pdfs(pdfunite, cover_pdf, output_pdf):
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    command = [pdfunite, str(cover_pdf), str(BODY_PDF), str(output_pdf)]
    subprocess.run(command, cwd=SOURCE_DIR, check=True)


def parse_arguments():
    parser = ArgumentParser(description="拼接 CPS 用户手册封面和正文 PDF")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="合并后的 PDF 路径，默认为 Docs/社区区域气候模式预处理系统用户手册.pdf",
    )
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    output_pdf = arguments.output
    if not output_pdf.is_absolute():
        output_pdf = DOCS_DIR / output_pdf

    require_file(BODY_PDF)
    require_file(COVER_SOURCE)
    xelatex = require_executable("xelatex")
    pdfunite = require_executable("pdfunite")

    with tempfile.TemporaryDirectory(prefix=".render-", dir=SOURCE_DIR) as temporary_dir:
        build_dir = Path(temporary_dir)
        cover_pdf = render_cover(xelatex, build_dir)
        merge_pdfs(pdfunite, cover_pdf, output_pdf)

    print(f"已生成：{output_pdf}")


if __name__ == "__main__":
    main()
