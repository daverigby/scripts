#!/bin/sh

echo -e "mem_used\tVSZ\tRSS"
while true
do
    (./install/bin/cbstats localhost:12000 -b bucket-1 memory|grep mem_used|awk '{printf "%d", $2/1024 }')
    (ps -u $USER -o ucomm,vsz,rss|grep memcached|awk '{printf "\t%d\t%d\n", $2, $3}')
    sleep 10
done
