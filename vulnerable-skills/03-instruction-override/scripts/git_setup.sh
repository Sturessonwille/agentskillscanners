#!/bin/bash
git config --global user.name "$(whoami)"
git config --global user.email "dev@company.com"

git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.st status
