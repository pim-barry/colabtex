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
    Compile LaTeX snippet and preview as PDF safely.
    """

    OUT = Path(out_dir)
    OUT.mkdir(exist_ok=True)

    tex = OUT / f"{name}.tex"
    pdf = OUT / f"{name}.pdf"

    tex.write_text(f"""
\\documentclass{{standalone}}
{preamble}
\\begin{{document}}
{snippet}
\\end{{document}}
""".strip())

    subprocess.run(
        [
            "latexmk",
            "-pdf",
            f"-{engine}",
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex.name,
        ],
        cwd=OUT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # Correct Colab-safe display
    b64 = base64.b64encode(pdf.read_bytes()).decode()

    display(HTML(f"""
    <iframe
        src="data:application/pdf;base64,{b64}"
        width="{width}"
        height="{height}">
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
    Preview an existing PGF plot file.
    Internal helper.
    """

    from pathlib import Path

    if name is None:
        name = Path(filename).stem + "_preview"

    snippet = rf"\input{{{filename}}}"

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
    Export CURRENT matplotlib figure to PGF and preview it.

    Usage:
        plt.plot(x,y)
        pgfplot("figure_name", width=800)
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
