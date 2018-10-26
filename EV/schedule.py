import datetime
import numpy as np
import math
import matplotlib.pyplot as plt
import recordtype
import sys

from abc import ABCMeta, abstractmethod
from datetime import datetime
from datetime import timedelta
from ortools.linear_solver import pywraplp
from recordtype import recordtype

EvJob = recordtype('EvJob', ['id', 'notify_time', 'start_time','end_time', 'demand_kwh', 'max_charging_rate'])

# Given a list of ev jobs, computes the offline optimal peak
def ComputeOptimalPeak(ev_jobs):
  time_horizon_start = datetime.max
  time_horizon_end = datetime.min
  for ev_job in ev_jobs:
    if ev_job.start_time < time_horizon_start:
      time_horizon_start = ev_job.start_time
    if ev_job.end_time > time_horizon_end:
      time_horizon_end = ev_job.end_time
  # The length of each slot is 900 seconds.
  slot_length_sec = 900.0
  num_slots = math.ceil((time_horizon_end - time_horizon_start).total_seconds() / slot_length_sec)
  solver = pywraplp.Solver('SolveSimpleSystem', pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
  peak = solver.NumVar(0, solver.infinity(), 'peak')
  peak_constraints = []
  for i in range(int(num_slots)):
    constraint = solver.Constraint(-solver.infinity(), 0.0)
    constraint.SetCoefficient(peak, -1)
    peak_constraints.append(constraint)
  charging_rate_vars = {i:[] for i in range(int(num_slots))}
  # print("*****")
  for ev_job in ev_jobs:
    start_sec = (ev_job.start_time - time_horizon_start).total_seconds()
    end_sec = (ev_job.end_time - time_horizon_start).total_seconds()
    start_index = int(math.floor(start_sec / slot_length_sec))
    time_after_start_sec = (start_index + 1) * slot_length_sec
    times = [start_sec]
    while time_after_start_sec < end_sec:
      times.append(time_after_start_sec)
      time_after_start_sec += slot_length_sec
    times.append(end_sec)
    max_demand = min(ev_job.demand_kwh, (ev_job.end_time - ev_job.start_time).total_seconds() * ev_job.max_charging_rate / 3600)
    # if max_demand < ev_job.demand_kwh:
      # print("Warning: job ", ev_job.id, " cannot be fully charged before deadline")
    charging_constraint = solver.Constraint(max_demand, max_demand)
    for i in range(len(times) - 1):
      charging_rate_var_name = str(ev_job.id + 'charging_rate' + str(i))
      charging_rate_vars[i + start_index].append(solver.NumVar(0, ev_job.max_charging_rate, charging_rate_var_name))
      size = len(charging_rate_vars[i + start_index])
      charging_constraint.SetCoefficient(charging_rate_vars[i + start_index][size - 1], (times[i+1] - times[i]) / 3600.0)
      peak_constraints[i + start_index].SetCoefficient(charging_rate_vars[i + start_index][size - 1], 1)
  objective = solver.Objective()
  objective.SetCoefficient(peak, 1)
  solver.Solve()
  total_rate = {}
  for i in range(int(num_slots)):
    total_rate[time_horizon_start + timedelta(seconds = i * slot_length_sec)] = sum([var.solution_value() for var in charging_rate_vars[i]])
  return peak.solution_value(), total_rate


class Scheduler:
  __metaclass__ = ABCMeta

  def __init__(self):
    self.all_jobs = []
    self.original_jobs = []
    self.schedule_history = {}
    self.num_unfinished_job = 0
    self.num_job = 0

  def AddEvJob(self, job_id, notify_time, arrival_time, end_time, demand, max_charging_rate):
    assert notify_time == arrival_time
    assert arrival_time >= self.current_time
    self.num_job += 1
    self.current_time = arrival_time
    self.all_jobs.append(EvJob(job_id, notify_time, arrival_time, end_time, demand, max_charging_rate))
    self.original_jobs.append(EvJob(job_id, notify_time, arrival_time, end_time, demand, max_charging_rate))

  @abstractmethod
  def Schedule(self, schedule_time):
    pass

  def TotalChargingRate(self, schedule_time):
    total = 0.0
    for job_id in self.schedule_history[schedule_time]:
      total += self.schedule_history[schedule_time][job_id]
    return total

  @abstractmethod
  def Name(self):
    pass

  @staticmethod
  def Plot(schedulers, time_period, show):
    if show:
      plt.figure()
    for scheduler in schedulers:
      times = []
      total_charging_rate = []
      for schedule_time in scheduler.schedule_history:
        times.append(schedule_time)
        total_charging_rate.append(scheduler.TotalChargingRate(schedule_time))
      if show:
        plt.scatter(times, total_charging_rate, label=scheduler.Name())
      print scheduler.Name(), "'s finish ratio: ", float(scheduler.num_unfinished_job)/scheduler.num_job, " peak: ", max(total_charging_rate)
    
    if show:
      plt.xlim(time_period)
      plt.legend()
      plt.show()


class MaxRateScheduler(Scheduler):

  def __init__(self):
    Scheduler.__init__(self)
    self.current_time = datetime.min
    self.last_schedule = {}
    self.last_schedule_time = datetime.min

  def Schedule(self, schedule_time):
    assert schedule_time >= self.last_schedule_time
    num_jobs = len(self.all_jobs)
    for idx in range(num_jobs - 1, -1, -1):
      job_id = self.all_jobs[idx].id
      if self.last_schedule.has_key(job_id):
        charged_kwh = self.last_schedule[job_id] * (schedule_time - self.last_schedule_time).total_seconds() / 3600.0
        self.all_jobs[idx].demand_kwh -= charged_kwh
	if self.all_jobs[idx].demand_kwh <= 0:
	  self.all_jobs.pop(idx)
    self.last_schedule.clear()
    # print ("**********")
    for job in self.all_jobs:
      self.last_schedule[job.id] = job.max_charging_rate
      # print(self.Name(), schedule_time, job.id, self.last_schedule[job.id])
    self.schedule_history[schedule_time] = self.last_schedule.copy()
    self.last_schedule_time = schedule_time

  def Name(self):
    return "Max scheduler"


class FixRateScheduler(Scheduler):

  def __init__(self):
    Scheduler.__init__(self)
    self.current_time = datetime.min
    self.last_schedule = {}
    self.last_schedule_time = datetime.min

  def Schedule(self, schedule_time):
    assert schedule_time >= self.last_schedule_time
    num_jobs = len(self.all_jobs)
    for idx in range(num_jobs - 1, -1, -1):
      job_id = self.all_jobs[idx].id
      if self.last_schedule.has_key(job_id):
        charged_kwh = self.last_schedule[job_id] * (schedule_time - self.last_schedule_time).total_seconds() / 3600.0
        self.all_jobs[idx].demand_kwh -= charged_kwh
	if self.all_jobs[idx].demand_kwh <= 1e-4:
	  self.all_jobs.pop(idx)
    self.last_schedule.clear()
    # print ("**********")
    for job in self.all_jobs:
      assert job.end_time > schedule_time
      self.last_schedule[job.id] = job.demand_kwh / (job.end_time - schedule_time).total_seconds() * 3600.0
      # print(self.Name(), schedule_time, job.id, self.last_schedule[job.id])
    self.schedule_history[schedule_time] = self.last_schedule.copy()
    self.last_schedule_time = schedule_time

  def Name(self):
    return "Fix rate scheduler"

class OracleScheduler(Scheduler):

  def __init__(self):
    Scheduler.__init__(self)
    self.current_time = datetime.min

  def Schedule(self, schedule_time):
    num_jobs = len(self.all_jobs)
    jobs = [job for job in self.all_jobs if job.start_time <= schedule_time]
    (peak, schedule) = ComputeOptimalPeak(jobs)
    # print("Oracle", peak, schedule_time)
    self.schedule_history.update(schedule)

  def Name(self):
    return "Offline optimal scheduler"

  def TotalChargingRate(self, schedule_time):
    return self.schedule_history[schedule_time]

class GreedyScheduler(Scheduler):

  def __init__(self, scale_factor=1.0):
    Scheduler.__init__(self)
    self.current_time = datetime.min
    self.last_schedule_time = datetime.min
    self.peak_history = {}
    self.scale_factor = scale_factor

  def GetJobBatch(self, ev_jobs, job_to_progress_deadline):
    job_batch = []
    cur_progress_deadline = datetime.min
    remaining_jobs = [job for job in ev_jobs if job.demand_kwh > 1e-4]
    for job in remaining_jobs:
      # print(job.start_time, job.end_time, job.demand_kwh)
      if job_to_progress_deadline[job] > cur_progress_deadline + timedelta(seconds=1):
        if len(job_batch) > 0:
          yield job_batch
        job_batch = [job]
        cur_progress_deadline = job_to_progress_deadline[job]
      elif job_to_progress_deadline[job] > cur_progress_deadline - timedelta(seconds=1):
        job_batch.append(job)
      else:
        sys.exit("jobs are not provided in order")
    if len(job_batch) > 0:
      yield job_batch
    yield []

  def UpdateJobDemand(self, ev_jobs, last_schedule_time, current_time):
    if last_schedule_time not in self.peak_history:
      return
    old_ev_jobs = [job for job in ev_jobs if job.start_time < current_time]
    total = self.peak_history[last_schedule_time]
    job_to_progress_deadline = {}
    for job in old_ev_jobs:
      job_to_progress_deadline[job] = job.end_time - timedelta(hours = job.demand_kwh / job.max_charging_rate)
    start = last_schedule_time
    while True:
      total_rate = total
      schedule = {}
      last_progress_deadline = datetime.min
      last = last_schedule_time
      arrived_jobs = [job for job in old_ev_jobs if job.start_time <= start and job.end_time > start]
      arrived_jobs.sort(key=lambda job: job_to_progress_deadline[job])
      duration = min([job.start_time for job in old_ev_jobs if job.start_time > start] + [current_time]) - start
      generator = self.GetJobBatch(arrived_jobs, job_to_progress_deadline)
      while True:
	job_batch = next(generator)
	if len(job_batch) == 0:
	  break
        total_max_charging_rate = 0.0
        for job in job_batch:
          total_max_charging_rate += job.max_charging_rate
        if total_max_charging_rate <= total_rate:
	  fraction = 1.0
        else:
          fraction = total_rate / total_max_charging_rate
	  current_progress_deadline = job_to_progress_deadline[job_batch[0]]
	  if last_progress_deadline > datetime.min and fraction < 1 - 1e-4:
	    duration = min(duration, timedelta(seconds=(current_progress_deadline - last_progress_deadline).total_seconds() / (1 - fraction)))
        last_progress_deadline = job_to_progress_deadline[job_batch[0]]
	for job in job_batch:
          schedule[job] = fraction
	  duration = min(duration, timedelta(hours=job.demand_kwh / schedule[job]))
	total_rate -= total_max_charging_rate
        if total_rate <= 1e-4:
	  next_job_batch = next(generator)
	  if len(next_job_batch) > 0 and fraction > 0:
	    duration = min(duration, timedelta(seconds=(job_to_progress_deadline[next_job_batch[0]] - last_progress_deadline).total_seconds() / fraction))
	  break
      # Update job_to_progress_deadline
      # print("total: ", duration.total_seconds())
      end = min(start + duration, current_time)
      duration = end - start
      for job in schedule:
        job_to_progress_deadline[job] += timedelta(seconds=(duration.total_seconds() * schedule[job]))
	job.demand_kwh -= job.max_charging_rate * schedule[job] * duration.total_seconds() / 3600.0
	# print(duration, schedule[job], job)
      start = end
      if start == current_time:
	break

  def GetTotalRate(self):
    (peak_charging_rate, dummy) = ComputeOptimalPeak(self.all_jobs)
    return peak_charging_rate * self.scale_factor

  def Schedule(self, schedule_time):
    assert schedule_time >= self.last_schedule_time
    self.schedule_history[schedule_time] = {}
    num_jobs = len(self.all_jobs)
    self.UpdateJobDemand(self.all_jobs, self.last_schedule_time, schedule_time)
    # print(self.all_jobs)
    for idx in range(num_jobs - 1, -1, -1):
      job_id = self.all_jobs[idx].id
      self.all_jobs[idx].start_time = schedule_time    
      if self.all_jobs[idx].end_time <= schedule_time and self.all_jobs[idx].demand_kwh > 1e-4:
	# print("Unfinished job: ", self.all_jobs[idx].id)
	self.num_unfinished_job += 1
      if self.all_jobs[idx].demand_kwh <= 1e-4 or self.all_jobs[idx].end_time <= schedule_time:
        self.all_jobs.pop(idx)

    peak_charging_rate = self.GetTotalRate()
    job_to_progress_deadline = {}
    total_max_charging_rate = 0.0
    for job in self.all_jobs:
      assert job.end_time > schedule_time
      total_max_charging_rate += job.max_charging_rate
    self.peak_history[schedule_time] = min(total_max_charging_rate, 1.4 * peak_charging_rate)
    self.last_schedule_time = schedule_time

  def Name(self):
    return "Greedy scheduler"

  def TotalChargingRate(self, schedule_time):
    return self.peak_history[schedule_time]

class EpsScheduler(GreedyScheduler):

  def __init__(self, scale_factor=1.0):
    GreedyScheduler.__init__(self, scale_factor)

  def GetTotalRate(self):
    (peak_charging_rate, dummy) = ComputeOptimalPeak(self.original_jobs)
    return peak_charging_rate * self.scale_factor

  def Name(self):
    return "Eps scheduler"

