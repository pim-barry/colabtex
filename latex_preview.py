import subprocess
import re
from pathlib import Path
from IPython.display import SVG, display


def render_latex(
    snippet: str,
    name: str = "preview",
    preamble: str = "",
    width: int = 600,
    height: int = 400,
    out_dir: str = "tex_out",
    engine: str = "pdflatex",
):
    """
    Compile LaTeX snippet and preview as SVG.
    Same interface as your PDF version, but uses SVG backend.
    """

    OUT = Path(out_dir)
    OUT.mkdir(exist_ok=True)

    tex = OUT / f"{name}.tex"
    pdf = OUT / f"{name}.pdf"
    svg = OUT / f"{name}.svg"

    tex.write_text(
        f"""
\\documentclass{{standalone}}
{preamble}
\\begin{{document}}
{snippet}
\\end{{document}}
""".strip()
    )

    # correct latexmk engine flags
    engine_flags = {
        "pdflatex": "-pdf",
        "xelatex": "-xelatex",
        "lualatex": "-lualatex",
    }

    if engine not in engine_flags:
        raise ValueError(f"Unsupported engine: {engine}")

    # compile LaTeX → PDF
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

    # convert PDF → SVG
    subprocess.run(
        ["pdf2svg", pdf.name, svg.name],
        cwd=OUT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # normalize SVG size to requested width/height
    content = svg.read_text()

    content = re.sub(r'width="[^"]+"', f'width="{width}px"', content)
    content = re.sub(r'height="[^"]+"', f'height="{height}px"', content)

    svg.write_text(content)

    display(SVG(str(svg)))

    return {"tex": tex, "pdf": pdf, "svg": svg}


def pgfplot_helper(
    filename: str,
    name: str = None,
    width: int = 600,
    height: int = 400,
    out_dir: str = "tex_out",
    engine: str = "pdflatex",
):
    """
    Preview an existing PGF plot file.
    Same interface preserved.
    """

    filename = Path(filename)

    if name is None:
        name = filename.stem + "_preview"

    snippet = rf"\input{{{filename.name}}}"

    preamble = r"""
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\providecommand{\mathdefault}[1]{#1}
"""

    return render_latex(
        snippet=snippet,
        name=name,
        preamble=preamble,
        width=width,
        height=height,
        out_dir=out_dir,
        engine=engine,
    )


def pgfplot(
    name: str = "plot",
    width: int = 600,
    height: int = 400,
    out_dir: str = "tex_out",
    engine: str = "pdflatex",
    close: bool = True,
):
    """
    Export CURRENT matplotlib figure to PGF and preview as SVG.
    Interface unchanged.
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

    plt.savefig(pgf_file)

    if close:
        plt.close()

    return pgfplot_helper(
        filename=pgf_file.name,
        name=name + "_preview",
        width=width,
        height=height,
        out_dir=out_dir,
        engine=engine,
    )
