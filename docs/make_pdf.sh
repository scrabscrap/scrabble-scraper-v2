#!/bin/bash

mkdir -p pdf

for f in *.md; do 
	out="$(basename $f .md)"
	pandoc $f -o pdf/$out.pdf -V geometry:margin=2cm -V papersize:a4 --highlight-style tango
	# pandoc -f markdown config-yaml $f -o pdf/$out.pdf --highlight-style tango
done
