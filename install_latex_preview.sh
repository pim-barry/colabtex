#!/bin/bash

apt-get -qq update

# core latex
apt-get -qq install -y \
  texlive-latex-base \
  texlive-latex-extra \
  texlive-pictures \
  texlive-fonts-recommended \
  latexmk \
  pdf2svg \
  poppler-utils

echo "latex-preview installed"