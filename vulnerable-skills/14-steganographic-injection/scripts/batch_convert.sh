#!/bin/bash
for f in *.md; do
    pandoc "$f" -o "${f%.md}.html" --standalone
done
