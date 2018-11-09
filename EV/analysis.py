from __future__ import print_function

import datetime
import math
import matplotlib.pyplot as plt
import numpy as np

from absl import app
from absl import flags

flags.DEFINE_string('dir', '', 'directory of the data')

FLAGS = flags.FLAGS

def ReadData(file):
  data = {}
  with open(FLAGS.dir + file) as f:
    content = f.readlines()
    for i in range(7):
      key = 1.0 + 0.05 * i
      value = []
      for item in content[i].split():
        value.append(float(item))
      data[key] = value
  return data

def main(argv):
  eps_peak = ReadData('eps_peak')
  greedy_peak = ReadData('greedy_peak')
  optimal_peak = ReadData('optimal_peak')
  eps_finish_ratio = ReadData('eps_finish_ratio')
  greedy_finish_ratio = ReadData('greedy_finish_ratio')
  num_days = len(eps_peak[1.0])
  plt.figure()
  keys = []
  greedy_crs = []
  eps_crs = []
  for key in optimal_peak:
    keys.append(key)
    greedy_cr = 0.0
    eps_cr = 0.0
    for i in range(num_days):
      ratio = greedy_peak[key][i] / optimal_peak[key][i]
      if ratio > greedy_cr:
        greedy_cr_idx = i
        greedy_cr = ratio
      # greedy_cr += greedy_peak[key][i] / optimal_peak[key][i]
      ratio = eps_peak[key][i] / optimal_peak[key][i]
      if ratio > eps_cr:
        eps_cr_idx = i
        eps_cr = ratio
      # eps_cr += eps_peak[key][i] / optimal_peak[key][i]
    print('worst case for greedy: ', greedy_cr_idx)
    print('worst case for eps: ', eps_cr_idx)
    greedy_crs.append(greedy_cr)
    eps_crs.append(eps_cr)
  plt.scatter(keys, greedy_crs, label='CR of greedy algorithm')
  plt.scatter(keys, eps_crs, label='CR of eps algorithm')
  plt.legend()

  plt.figure()
  keys = []
  greedy_ratios = []
  eps_ratios = []
  for key in optimal_peak:
    keys.append(key)
    greedy_ratio = 0.0
    eps_ratio = 0.0
    for i in range(num_days):
      greedy_ratio += greedy_finish_ratio[key][i]
      eps_ratio += eps_finish_ratio[key][i]
    greedy_ratio /= num_days
    eps_ratio /= num_days
    greedy_ratios.append(greedy_ratio)
    eps_ratios.append(eps_ratio)
  plt.scatter(keys, greedy_ratios, label='Unfinish rate of greedy algorithm')
  plt.scatter(keys, eps_ratios, label='Unfinish rate of eps algorithm')
  plt.legend()
  plt.show()

if __name__ == '__main__':
  app.run(main)
