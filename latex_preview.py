import subprocess
import base64
from pathlib import Path
from IPython.display import HTML, display


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
    Compile LaTeX snippet and preview as embedded PDF.
    Fully self-contained and robust.
    """

    OUT = Path(out_dir)
    OUT.mkdir(exist_ok=True)

    tex = OUT / f"{name}.tex"
    pdf = OUT / f"{name}.pdf"

    tex.write_text(
        f"""
\\documentclass{{standalone}}
{preamble}
\\begin{{document}}
{snippet}
\\end{{document}}
""".strip()
    )

    # Correct latexmk engine handling
    engine_flags = {
        "pdflatex": "-pdf",
        "xelatex": "-xelatex",
        "lualatex": "-lualatex",
    }

    if engine not in engine_flags:
        raise ValueError(f"Unsupported engine: {engine}")

    cmd = [
        "latexmk",
        engine_flags[engine],
        "-interaction=nonstopmode",
        "-halt-on-error",
        tex.name,
    ]

    subprocess.run(
        cmd,
        cwd=OUT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # Embed PDF safely
    b64 = base64.b64encode(pdf.read_bytes()).decode()

    display(HTML(f"""
    <iframe
        src="data:application/pdf;base64,{b64}"
        width="{width}"
        height="{height}"
        style="border:none;">
    </iframe>
    """))

    return {"tex": tex, "pdf": pdf}


def pgfplot_helper(
    filename: str,
    name: str = None,
    width: int = 600,
    height: int = 400,
    out_dir: str = "tex_out",
    engine: str = "pdflatex",
):
    """
    Preview an existing PGF file.
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
    Export current matplotlib figure to PGF and preview.
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
