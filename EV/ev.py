from __future__ import print_function

import collections
import datetime
import json

import schedule

from absl import app
from absl import flags
from ortools.linear_solver import pywraplp

FLAGS = flags.FLAGS
Scheduler = schedule.Scheduler

EvRecord = collections.namedtuple('EvRecord', ['id','start_time','end_time', 'energy_charged_kwh', 'done_charging', 'location']) 

flags.DEFINE_float('scale', 1.0, 'scaling factor')

def ToDateTime(epoc_time_ms):
  epoc_time_s = float(epoc_time_ms) / 1000.0
  return datetime.datetime.fromtimestamp(epoc_time_s)

def LoadData(start_time, end_time):
  with open("./Caltech_ACN_Apr_15_Sept_18.json") as data_file:
    number = next(data_file).strip()
    jsons = [json.loads(line) for line in data_file]
  records = []
  for line in jsons:
    record_start_time = ToDateTime(line['start']['$date']['$numberLong'])
    if record_start_time < start_time:
      continue
    record_end_time = ToDateTime(line['end']['$date']['$numberLong'])
    if record_end_time > end_time:
      continue
    records.append(EvRecord(line['_id']['$oid'], record_start_time, record_end_time, float(line['kWh_delivered']['$numberDouble']),
			    ToDateTime(line['done_charging']['$date']['$numberLong']), line['space_number']))
  records.sort(key=lambda record : record.start_time)
  return records

def ToHours(time_delta):
  return time_delta.total_seconds() / 3600.0

def DataBatch(data, stime, delta):
  batch = []
  start_time = stime
  for d in data:
    if d.start_time > start_time + delta:
      yield batch
      batch = [d]
      start_time += delta
    else:
      batch.append(d)
  yield batch

def main(argv):
  time_period = [datetime.datetime(2018, 4, 16, 21, 0, 0), datetime.datetime(2018, 9, 16, 21, 0, 0)]
  data = LoadData(time_period[0], time_period[1])
  # data = [EvRecord('1', datetime.datetime(2018, 4, 18, 0, 0, 0), datetime.datetime(2018, 4, 18, 1, 0, 0), 20, datetime.datetime(2018, 4, 18, 0, 30, 0), '121'), EvRecord('2', datetime.datetime(2018, 4, 18, 0, 30, 0), datetime.datetime(2018, 4, 18, 2, 0, 0), 30, datetime.datetime(2018, 4, 18, 1, 0, 0), '122'), EvRecord('3', datetime.datetime(2018, 4, 18, 1, 0, 0), datetime.datetime(2018, 4, 18, 3, 0, 0), 25, datetime.datetime(2018, 4, 18, 2, 0, 0), '123')]

  for data in DataBatch(LoadData(time_period[0], time_period[1]), time_period[0], datetime.timedelta(hours=24)):
    # continuous_schedulers = [schedule.MaxRateScheduler(), schedule.FixRateScheduler()]
    continuous_schedulers = []
    slotted_schedulers = [schedule.GreedyScheduler(FLAGS.scale), schedule.EpsScheduler(FLAGS.scale)]
    # slotted_schedulers = []
    offline_schedulers = [schedule.OracleScheduler()]
    last_schedule_time = datetime.datetime.min
    schedule_slot = datetime.timedelta(minutes=15)
    for record in data:
      max_charging_rate = record.energy_charged_kwh / ToHours(record.done_charging - record.start_time)
      for scheduler in continuous_schedulers:
        scheduler.AddEvJob(record.id, record.start_time, record.start_time, record.end_time, record.energy_charged_kwh, max_charging_rate)
        scheduler.Schedule(record.start_time)
      for scheduler in slotted_schedulers + offline_schedulers:
        scheduler.AddEvJob(record.id, record.start_time, record.start_time, record.end_time, record.energy_charged_kwh, max_charging_rate)
      if record.start_time > last_schedule_time + schedule_slot:
        for scheduler in slotted_schedulers:
          scheduler.Schedule(record.start_time)
        last_schedule_time = record.start_time
    for scheduler in offline_schedulers:
      scheduler.Schedule(datetime.datetime.max)
    Scheduler.Plot(continuous_schedulers + slotted_schedulers + offline_schedulers, time_period, False)
  """
  ev_jobs = [schedule.EvJob('1', datetime.datetime(2018, 4, 18, 0, 10), datetime.datetime(2018, 4, 18, 0, 10), datetime.datetime(2018, 4, 18, 2, 15), 3, 2), schedule.EvJob('2', datetime.datetime(2018, 4, 18, 0, 0), datetime.datetime(2018, 4, 18, 0, 0), datetime.datetime(2018, 4, 18, 3, 0), 6, 2)]
  print("Solution:", schedule.ComputeOptimalPeak(ev_jobs))
  """


if __name__ == '__main__':
  app.run(main)
