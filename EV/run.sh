#!/bin/bash
for ratio in 1.0 1.05 1.1 1.15 1.2 1.25 1.3;
do
	echo "Running: "$ratio
	python ev.py --scale=$ratio > result/scale=$ratio
done
