#!/bin/bash

# Man Page
txt2tags -t man -i videocache.8.t2t -o videocache.8
gzip -f videocache.8

# HTML
txt2tags -t html --toc -i videocache.8.t2t -o Readme.html

# PDF
#rm -f Readme.aux Readme.log Readme.out Readme.toc Readme.toc Readme.dvi Readme.tex
#txt2tags -t tex -i videocache.8.t2t -o Readme.tex
#pdflatex Readme.tex > /dev/null 2> /dev/null
#rm -f Readme.aux Readme.log Readme.out Readme.toc Readme.toc Readme.dvi Readme.tex
