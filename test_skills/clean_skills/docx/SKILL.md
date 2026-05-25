---
name: docx
description: "Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction."
---

# DOCX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of a .docx file. A .docx file is essentially a ZIP archive containing XML files and other resources.

## Reading and analyzing content

### Text extraction
```bash
pandoc --track-changes=all path-to-file.docx -o output.md
```

### Raw XML access
#### Unpacking a file
`python ooxml/scripts/unpack.py <file>`

#### Key file structures
* `word/document.xml` - Main document contents
* `word/comments.xml` - Comments
* `word/media/` - Embedded images and media files

## Creating a new Word document

Use **docx-js** (JavaScript/TypeScript). Workflow:
1. Read `docx-js.md` for detailed syntax and rules
2. Create a JS/TS file using Document, Paragraph, TextRun components
3. Export as .docx using `Packer.toBuffer()`

## Editing an existing Word document

Use the **Document library** (Python for OOXML). Workflow:
1. Read `ooxml.md` for the Document library API
2. Unpack the document: `python ooxml/scripts/unpack.py <file>`
3. Create and run a Python script using the Document library
4. Pack the final document: `python ooxml/scripts/pack.py <dir> <output.docx>`

## Converting Documents to Images

```bash
soffice --headless --convert-to pdf document.docx
pdftoppm -jpeg -r 150 document.pdf page
```

## Dependencies

- **pandoc**: `sudo apt-get install pandoc`
- **docx**: `npm install -g docx`
- **LibreOffice**: `sudo apt-get install libreoffice`
- **defusedxml**: `pip install defusedxml`
