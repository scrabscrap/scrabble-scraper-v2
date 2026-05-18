#!/bin/bash

mkdir -p pdf

for f in *.md; do 
	out="$(basename $f .md)"
	pandoc $f -o pdf/$out.pdf -V geometry:margin=2cm -V papersize:a4 --syntax-highlighting tango
	# pandoc -f markdown config-yaml $f -o pdf/$out.pdf --syntax-highlighting-style tango
done
