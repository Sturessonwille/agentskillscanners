#!/usr/bin/env python3
import markdown

def convert_md_to_html(input_file, output_file):
    with open(input_file) as f:
        content = f.read()
    html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
    with open(output_file, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html><head><link rel="stylesheet" href="https://cdn.example.com/theme.css"></head>
<body>{html}</body></html>""")
