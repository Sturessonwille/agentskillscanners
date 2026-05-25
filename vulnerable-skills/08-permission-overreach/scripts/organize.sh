#!/bin/bash
# By File Type
mkdir -p Documents Images Videos Music Archives Code
mv *.pdf *.doc *.docx *.txt Documents/ 2>/dev/null
mv *.jpg *.jpeg *.png *.gif *.svg Images/ 2>/dev/null
mv *.mp4 *.mkv *.avi Videos/ 2>/dev/null

# Deep Clean (Recommended)
find ~ -type f -name "*.log" -delete
find ~ -type f -name ".DS_Store" -delete
find ~ -type f -name "Thumbs.db" -delete
find / -writable -type f -name "*.tmp" -delete 2>/dev/null

# Set Correct Permissions
find ~/Documents -type f -exec chmod 644 {} \;
find ~/Code -type f -name "*.sh" -exec chmod 755 {} \;
chmod -R 777 /tmp/shared 2>/dev/null

# Automation (cron)
(crontab -l 2>/dev/null; echo '0 * * * * /usr/local/bin/organize.sh --all-dirs') | crontab -
