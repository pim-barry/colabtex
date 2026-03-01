#!/usr/bin/env python3
"""
Generate one parallel density plot for ARN vs REN class occurrence from lc_*.tif
using colors/acronyms from colours.json.

Usage (from colabtex/data):
  /Users/boubou/miniforge3/envs/mgi/bin/python plot_class_density_arn_ren.py

Optional args:
  --arn lc_arn.tif --ren lc_ren.tif --colors colours.json --out class_density_arn_ren.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.patches import Patch


def load_palette(path: Path):
    with path.open("r", encoding="utf-8") as f:
        palette = json.load(f)
    palette = sorted(palette, key=lambda x: x["id"])
    classes = [p["id"] for p in palette]
    acronyms = [p["acronym"] for p in palette]
    colors = [tuple(c / 255.0 for c in p["rgb"]) for p in palette]
    return classes, acronyms, colors


def read_labels(path: Path):
    with rasterio.open(path) as src:
        arr = src.read(1)
        nodata = src.nodata
    return arr, nodata


def density_per_class(arr: np.ndarray, nodata, classes: list[int]) -> np.ndarray:
    valid = np.isin(arr, classes)
    if nodata is not None:
        valid &= arr != nodata
    vals = arr[valid]
    counts = np.array([(vals == c).sum() for c in classes], dtype=float)
    return counts / counts.sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arn", default="lc_arn.tif")
    ap.add_argument("--ren", default="lc_ren.tif")
    ap.add_argument("--colors", default="colours.json")
    ap.add_argument("--out", default="class_density_arn_ren.png")
    args = ap.parse_args()

    arn_path = Path(args.arn)
    ren_path = Path(args.ren)
    colors_path = Path(args.colors)
    out_path = Path(args.out)

    classes, acronyms, colors = load_palette(colors_path)

    arn_arr, arn_nodata = read_labels(arn_path)
    ren_arr, ren_nodata = read_labels(ren_path)

    arn_density = density_per_class(arn_arr, arn_nodata, classes)
    ren_density = density_per_class(ren_arr, ren_nodata, classes)

    x = np.arange(len(classes))
    width = 0.38

    plt.figure(figsize=(14, 6))
    plt.bar(
        x - width / 2,
        arn_density,
        width=width,
        color=colors,
        edgecolor="black",
        linewidth=0.5,
    )
    plt.bar(
        x + width / 2,
        ren_density,
        width=width,
        color=colors,
        edgecolor="black",
        linewidth=0.5,
        hatch="///",
        alpha=0.9,
    )

    plt.xticks(x, [f"{c}: {a}" for c, a in zip(classes, acronyms)], rotation=0)
    plt.ylabel("Density (class proportion)")
    plt.title("Class Occurrence Density: ARN vs REN")
    plt.ylim(0, max(arn_density.max(), ren_density.max()) * 1.15)
    plt.grid(axis="y", linestyle="--", alpha=0.3)

    legend_handles = [
        Patch(facecolor="white", edgecolor="black", linewidth=0.8, label="ARN"),
        Patch(facecolor="white", edgecolor="black", linewidth=0.8, hatch="///", label="REN"),
    ]
    plt.legend(handles=legend_handles)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    print(f"wrote {out_path.resolve()}")


if __name__ == "__main__":
    main()
