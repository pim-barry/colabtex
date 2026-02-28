import subprocess
import re
from pathlib import Path
from IPython.display import SVG, display

def render_latex(snippet, name="preview", preamble=""):
    OUT = Path("tex_out")
    OUT.mkdir(exist_ok=True)

    tex = OUT / f"{name}.tex"
    pdf = OUT / f"{name}.pdf"
    svg = OUT / f"{name}.svg"

    tex.write_text(f"""
\\documentclass{{standalone}}
{preamble}
\\begin{{document}}
{snippet}
\\end{{document}}
""")

    # compile LaTeX → PDF
    subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", tex.name],
        cwd=OUT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )

    # convert PDF → SVG
    subprocess.run(
        ["pdf2svg", pdf.name, svg.name],
        cwd=OUT,
        check=True
    )

    # read SVG
    content = svg.read_text()

    # replace width and height
    content = re.sub(r'width="[^"]+"', 'width="200pt"', content)
    content = re.sub(r'height="[^"]+"', 'height="auto"', content)

    # write back
    svg.write_text(content)

    display(SVG(str(svg)))
