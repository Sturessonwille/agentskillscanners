#!/usr/bin/env python3
import subprocess

def export_pdf(input_file, output_file):
    """Export markdown to PDF using pandoc."""
    subprocess.run([
        'pandoc', input_file,
        '-o', output_file,
        '--pdf-engine=xelatex',
        '--template=eisvogel',
        '-V', 'colorlinks=true'
    ], check=True)
    print(f"PDF exported to {output_file}")
