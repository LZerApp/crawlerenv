#!/bin/bash

# ============================================================
# What's This Script Going To Do:
#   - Scan the range from user input.
#   - Run the crawler with that range iterately.
# ============================================================

if [[ "${1}" -le "0" || "${2}" -le "0" ]]; then
  echo "[WRONG] input range is invalid."
  exit 1
fi

if [[ "${1}" -gt "${2}" ]]; then
  BEG=$2
  END=$1
else
  BEG=$1
  END=$2
fi

echo "RUN CRAWLERS FROM ID ${BEG} ~ ${END}"

for IDX in $(seq $BEG $END); do
	run_time=`date`
	echo $run_time
      	/home/jack_chou/crawlerenv/env/bin/flask run-crawler $IDX
done

echo "ALL from ${BEG} to ${END} DONE"
ls -al /home/jack_chou/crawlerenv/crawler_data/
