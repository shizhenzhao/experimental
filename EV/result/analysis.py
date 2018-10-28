from __future__ import print_function

import datetime
import math
import matplotlib.pyplot as plt
import numpy as np

from absl import app

def ReadData(file):
  data = {}
  with open(file) as f:
    content = f.readlines()
    for i in range(7):
      key = 1.0 + 0.05 * i
      value = []
      for item in content[i].split():
        value.append(float(item))
      print(len(value))
      data[key] = value
  return data

def main(argv):
  eps_peak = ReadData('eps_peak')
  greedy_peak = ReadData('greedy_peak')
  eps_peak = ReadData('eps_peak')
  eps_peak = ReadData('eps_peak')
  eps_peak = ReadData('eps_peak')
  eps_peak = ReadData('eps_peak')

if __name__ == '__main__':
  app.run(main)
