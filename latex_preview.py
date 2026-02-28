import subprocess
from pathlib import Path
from IPython.display import HTML, display


def render_latex(
    snippet: str,
    name: str = "preview",
    preamble: str = "",
    width_pt: int = 500,
    out_dir: str = "tex_out",
    engine: str = "pdflatex",
):
    """
    Compile LaTeX snippet and preview as SVG (robust, no XML parsing errors).

    Self-contained, portable, safe.

    Parameters
    ----------
    snippet : LaTeX snippet (no wrapper needed)
    name : output filename base
    preamble : extra LaTeX preamble
    width_pt : display width in points
    out_dir : output directory
    engine : pdflatex, xelatex, or lualatex
    """

    OUT = Path(out_dir)
    OUT.mkdir(exist_ok=True)

    tex = OUT / f"{name}.tex"
    pdf = OUT / f"{name}.pdf"
    svg = OUT / f"{name}.svg"

    # Write LaTeX file
    tex.write_text(
        f"""
\\documentclass{{standalone}}
{preamble}
\\begin{{document}}
{snippet}
\\end{{document}}
""".strip()
    )

    # Compile LaTeX → PDF
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

    # Convert PDF → SVG
    subprocess.run(
        ["pdf2svg", pdf.name, svg.name],
        cwd=OUT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # Read SVG content
    svg_content = svg.read_text()

    # Display SVG safely (no XML parsing)
    display(
        HTML(
            f'''
<div style="width:{width_pt}pt">
{svg_content}
</div>
'''
        )
    )

    return {
        "tex": tex,
        "pdf": pdf,
        "svg": svg,
    }