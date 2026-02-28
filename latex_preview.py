import subprocess, re
from pathlib import Path
from IPython.display import SVG, display

def render_latex(snippet, name="preview", preamble="", width_pt=500, out_dir="tex_out"):
    OUT = Path(out_dir)
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

    subprocess.run(
        ["latexmk","-pdf","-interaction=nonstopmode",tex.name],
        cwd=OUT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
    )

    subprocess.run(
        ["pdf2svg",pdf.name,svg.name],
        cwd=OUT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
    )

    # scale svg cleanly
    content = svg.read_text()
    content = re.sub(r'<svg ', f'<svg width="{width_pt}pt" ', content, count=1)
    svg.write_text(content)

    display(SVG(str(svg)))