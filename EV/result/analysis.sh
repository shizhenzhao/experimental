#!/bin/bash
>peak
for scale in 1.0 1.05 1.1 1.15 1.2 1.25 1.3;
do
  filename=(scale=$scale)
  finish_ratio_greedy=$(grep Greedy $filename | awk '{print $6}')
  peak_greedy=$(grep Greedy $filename | awk '{print $8}')
  finish_ratio_eps=$(grep Eps $filename | awk '{print $6}')
  peak_eps=$(grep Eps $filename | awk '{print $8}')
  finish_ratio_offline=$(grep Offline $filename | awk '{print $7}')
  peak_offline=$(grep Offline $filename | awk '{print $9}')
  echo $filename >> peak
  echo $peak_greedy >> peak
  echo $peak_eps >> peak
  echo $peak_offline >> peak
done
