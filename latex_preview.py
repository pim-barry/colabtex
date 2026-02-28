import subprocess
import re
from pathlib import Path
from IPython.display import SVG, display


def render_latex(
    snippet: str,
    name: str = "preview",
    preamble: str = "",
    width_pt: int = 500,
    out_dir: str = "tex_out",
    engine: str = "pdflatex",
):
    """
    Compile a LaTeX snippet and preview it as SVG inside a notebook.

    Parameters
    ----------
    snippet : str
        LaTeX code to render (no document wrapper needed).

    name : str
        Base filename for generated files.

    preamble : str
        Extra LaTeX preamble (e.g., \\usepackage{booktabs})

    width_pt : int
        Display width in points (vector scaled, no quality loss)

    out_dir : str
        Directory where outputs are stored

    engine : str
        LaTeX engine (pdflatex, xelatex, lualatex)
    """

    OUT = Path(out_dir)
    OUT.mkdir(exist_ok=True)

    tex = OUT / f"{name}.tex"
    pdf = OUT / f"{name}.pdf"
    svg = OUT / f"{name}.svg"

    # write LaTeX wrapper
    tex.write_text(
        f"""
\\documentclass{{standalone}}
{preamble}
\\begin{{document}}
{snippet}
\\end{{document}}
""".strip()
    )

    # compile LaTeX → PDF
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

    # convert PDF → SVG
    subprocess.run(
        ["pdf2svg", pdf.name, svg.name],
        cwd=OUT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # safely scale SVG (remove existing width/height first)
    content = svg.read_text()

    content = re.sub(r'\swidth="[^"]+"', "", content)
    content = re.sub(r'\sheight="[^"]+"', "", content)

    content = re.sub(
        r"<svg",
        f'<svg width="{width_pt}pt"',
        content,
        count=1,
    )

    svg.write_text(content)

    # display SVG preview
    display(SVG(str(svg)))

    return {
        "tex": tex,
        "pdf": pdf,
        "svg": svg,
    }
