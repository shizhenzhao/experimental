#!/bin/bash
>greedy_peak
>eps_peak
>optimal_peak
>greedy_finish_ratio
>eps_finish_ratio
>optimal_finish_ratio
for scale in 1.0 1.05 1.1 1.15 1.2 1.25 1.3;
do
  filename=(scale=$scale)
  finish_ratio_greedy=$(grep Greedy $filename | awk '{print $6}')
  peak_greedy=$(grep Greedy $filename | awk '{print $8}')
  finish_ratio_eps=$(grep Eps $filename | awk '{print $6}')
  peak_eps=$(grep Eps $filename | awk '{print $8}')
  finish_ratio_offline=$(grep Offline $filename | awk '{print $7}')
  peak_offline=$(grep Offline $filename | awk '{print $9}')
  echo $peak_greedy >> greedy_peak
  echo $peak_eps >> eps_peak
  echo $peak_offline >> optimal_peak
  echo $finish_ratio_greedy >> greedy_finish_ratio
  echo $finish_ratio_eps >> eps_finish_ratio
  echo $finish_ratio_offline >> optimal_finish_ratio
done
