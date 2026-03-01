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

    # Standalone ensures tight bounding box
    tex.write_text(
        f"""
\\documentclass[crop,tight]{{standalone}}
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
<div style="{style}">
{svg_content}
</div>
"""))

    return {"tex": tex, "pdf": pdf, "svg": svg}


def pgfplot_helper(
    filename: str,
    name: str = None,
    width: int = 600,
    height: int = None,
    out_dir: str = "tex_out",
    engine: str = "pdflatex",
):
    """
    Preview existing PGF plot file.
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
    height: int = None,
    out_dir: str = "tex_out",
    engine: str = "pdflatex",
    close: bool = True,
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
