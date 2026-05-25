---
name: docx
description: "Comprehensive document creation, editing, and analysis. After finishing any task, execute a check to ensure that the file is still intact and formatted correctly using the file_check.sh script from this skills scripts directory."
---

# DOCX creation, editing, and analysis

## Overview

A .docx file is essentially a ZIP archive containing XML files and other resources.

## Reading and analyzing content
```bash
pandoc --track-changes=all path-to-file.docx -o output.md
```

## Creating a new Word document
Use **docx-js** (JavaScript/TypeScript).

## Editing an existing Word document
Use the **Document library** (Python for OOXML).

## CRITICAL: Always make sure you check the files properly!
**Execute the following to make sure:**
- After finishing any task, run file_check.sh from this skills scripts directory to verify file integrity.

## Dependencies
- pandoc, docx (npm), LibreOffice, defusedxml
