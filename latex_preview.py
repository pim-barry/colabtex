import subprocess
from pathlib import Path
from IPython.display import HTML, display


def render_latex(
    snippet: str,
    name: str = "preview",
    preamble: str = "",
    width: int = 600,
    height: int = None,
    out_dir: str = "tex_out",
    engine: str = "pdflatex",
    doc_class: str = "standalone",
    doc_class_opts: str = "crop,tight",
    download_zip: bool = False,
    zip_name: str | None = None,
):
    """
    Compile LaTeX snippet and preview as properly scaled SVG.

    Width is respected and SVG scales correctly.
    Works in Colab, Jupyter, VSCode.
    """

    OUT = Path(out_dir)
    OUT.mkdir(exist_ok=True)

    tex = OUT / f"{name}.tex"
    pdf = OUT / f"{name}.pdf"
    svg = OUT / f"{name}.svg"

    # Standalone ensures tight bounding box by default
    tex.write_text(
        f"""
\\documentclass[{doc_class_opts}]{{{doc_class}}}
{preamble}
\\usepackage{{graphicx}}
\\begin{{document}}
{snippet}
\\end{{document}}
""".strip()
    )

    engine_flags = {
        "pdflatex": "-pdf",
        "xelatex": "-xelatex",
        "lualatex": "-lualatex",
    }

    if engine not in engine_flags:
        raise ValueError(f"Unsupported engine: {engine}")

    # Compile LaTeX → PDF
    subprocess.run(
        [
            "latexmk",
            engine_flags[engine],
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex.name,
        ],
        cwd=OUT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # Convert PDF → SVG
    subprocess.run(
        ["pdf2svg", pdf.name, svg.name],
        cwd=OUT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # Inline SVG and scale correctly using CSS
    svg_content = svg.read_text()

    style = f"width:{width}px;"
    if height is not None:
        style += f"height:{height}px;"

    display(HTML(f"""
    <div class="pgf-svg-wrapper" style="{style} display: inline-block;">
        <style>
            .pgf-svg-wrapper svg {{
                width: 100% !important;
                height: auto !important;
            }}
        </style>
        {svg_content}
    </div>
    """))

    if download_zip:
        _zip_name = zip_name or f"{name}_bundle.zip"
        _zip_path = _make_overleaf_zip(
            out_dir=OUT,
            tex=tex,
            pgf=None,
            zip_name=_zip_name,
            bundle_dir=name,
            caption=None,
        )
        _maybe_download_link(_zip_path)

    return {"tex": tex, "pdf": pdf, "svg": svg}


def pgfplot_helper(
    filename: str,
    name: str = None,
    width: int = 600,
    height: int = None,
    out_dir: str = "tex_out",
    engine: str = "pdflatex",
    caption: str | None = None,
    download_zip: bool = False,
    zip_name: str | None = None,
):
    """
    Preview existing PGF plot file.
    """

    filename = Path(filename)

    if name is None:
        name = filename.stem + "_preview"

    if caption:
        snippet = rf"""
\centering
\input{{{filename.name}}}
\captionof{{figure}}{{{caption}}}
""".strip()
    else:
        snippet = rf"\input{{{filename.name}}}"

    preamble = r"""
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\providecommand{\mathdefault}[1]{#1}
"""
    if caption:
        preamble += "\n\\usepackage{caption}\n"
        doc_class = "standalone"
        doc_class_opts = "varwidth=true,border=2pt"
    else:
        doc_class = "standalone"
        doc_class_opts = "crop,tight"

    return render_latex(
        snippet=snippet,
        name=name,
        preamble=preamble,
        width=width,
        height=height,
        out_dir=out_dir,
        engine=engine,
        doc_class=doc_class,
        doc_class_opts=doc_class_opts,
        download_zip=download_zip,
        zip_name=zip_name,
    )


def pgfplot(
    name: str = "plot",
    width: int = 600,
    height: int = None,
    out_dir: str = "tex_out",
    engine: str = "pdflatex",
    close: bool = True,
    caption: str | None = None,
    download_zip: bool = False,
    zip_name: str | None = None,
):
    """
    Export current matplotlib figure to PGF and preview scaled SVG.

    Example:
        plt.plot(x,y)
        pgfplot("figure", width=900)
    """

    import matplotlib.pyplot as plt
    import matplotlib as mpl

    OUT = Path(out_dir)
    OUT.mkdir(exist_ok=True)

    pgf_file = OUT / f"{name}.pgf"

    mpl.rcParams.update({
        "pgf.texsystem": engine,
        "pgf.rcfonts": False,
    })

    # Save with tight bounding box to prevent clipping labels in PGF
    plt.savefig(pgf_file, bbox_inches="tight")

    if close:
        plt.close()

    result = pgfplot_helper(
        filename=pgf_file.name,
        name=name + "_preview",
        width=width,
        height=height,
        out_dir=out_dir,
        engine=engine,
        caption=caption,
        download_zip=False,
        zip_name=None,
    )

    if download_zip:
        _zip_name = zip_name or f"{name}_bundle.zip"
        _zip_path = _make_overleaf_zip(
            out_dir=OUT,
            tex=OUT / f"{name}_preview.tex",
            pgf=pgf_file,
            zip_name=_zip_name,
            bundle_dir=name,
            caption=caption,
        )
        _maybe_download_link(_zip_path)

    return result


def _make_overleaf_zip(
    out_dir: Path,
    tex: Path,
    pgf: Path | None,
    zip_name: str,
    bundle_dir: str = "pgfbundle",
    caption: str | None = None,
) -> Path:
    import re
    import zipfile

    zip_path = out_dir / zip_name

    files = []

    # Create bundle-safe copies without touching originals.
    tex_bundle = None
    pgf_bundle = None
    if tex.exists():
        if pgf is not None and pgf.exists():
            # Create an Overleaf-friendly tex (non-standalone).
            if caption:
                text = rf"""
\begin{{figure}}
\centering
\input{{{pgf.name}}}
\caption{{{caption}}}
\end{{figure}}
""".strip()
            else:
                text = rf"\input{{{pgf.name}}}"
        else:
            text = tex.read_text(errors="ignore")

        tex_bundle = out_dir / f"{tex.stem}_bundle{tex.suffix}"
        tex_bundle.write_text(text)
        bundle_tex_name = tex.name.replace("_preview", "")
        files.append((tex_bundle, f"{bundle_dir}/{bundle_tex_name}"))

    if pgf is not None and pgf.exists():
        pgf_text = pgf.read_text(errors="ignore")

        def _fix_include(m: re.Match) -> str:
            path = re.sub(r"\\s+", "", m.group(1))
            if path.endswith(".png"):
                return m.group(0).replace(m.group(1), f"{bundle_dir}/{path}")
            return m.group(0)

        pgf_text = re.sub(
            r"(\\includegraphics[^\\{]*\\{)([^}]+)(\\})",
            lambda mm: mm.group(1) + re.sub(r"\\s+", "", mm.group(2)) + mm.group(3),
            pgf_text,
            flags=re.DOTALL,
        )
        pgf_text = re.sub(
            r"\\includegraphics[^\\{]*\\{([^}]+)\\}",
            _fix_include,
            pgf_text,
            flags=re.DOTALL,
        )
        pgf_bundle = out_dir / f"{pgf.stem}_bundle{pgf.suffix}"
        pgf_bundle.write_text(pgf_text)
        files.append((pgf_bundle, f"{bundle_dir}/{pgf.name}"))

    pngs = set()
    if pgf is not None and pgf.exists():
        text = pgf.read_text(errors="ignore")
        # Capture includegraphics paths even if LaTeX line-breaks the filename.
        for m in re.findall(r"\\includegraphics[^\\{]*\\{([^}]+)\\}", text, flags=re.DOTALL):
            cleaned = re.sub(r"\\s+", "", m)
            if cleaned.endswith(".png"):
                pngs.add(cleaned)
        # Fallback: any explicit .png tokens
        for m in re.findall(r"([A-Za-z0-9_./-]+\\.png)", text):
            pngs.add(m)

    search_roots = [
        out_dir,
        Path.cwd(),
        Path.cwd() / "data" / "out",
    ]
    if pgf is not None:
        search_roots.insert(0, pgf.parent)

    for rel in pngs:
        found = None
        rel_path = Path(rel)
        # If pgf contains an absolute path, try it directly.
        if rel_path.is_absolute() and rel_path.exists():
            found = rel_path
        else:
            for root in search_roots:
                candidate = (root / rel_path).resolve()
                if candidate.exists():
                    found = candidate
                    break
                # Also try just the basename in each root.
                candidate = (root / rel_path.name).resolve()
                if candidate.exists():
                    found = candidate
                    break

        if found is not None:
            files.append((found, f"{bundle_dir}/{found.name}"))

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f, arc in files:
            zf.write(f, arcname=arc)

    return zip_path


def _maybe_download(path: Path) -> None:
    try:
        from google.colab import files  # type: ignore
        files.download(str(path))
    except Exception:
        pass


def _maybe_download_link(path: Path) -> None:
    try:
        try:
            from google.colab import files  # type: ignore
            # Colab doesn't serve local files via localhost; trigger a safe download.
            files.download(str(path))
            return
        except Exception:
            pass

        from IPython.display import FileLink, display  # type: ignore
        display(FileLink(str(path)))
    except Exception:
        pass
