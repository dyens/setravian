import logging
import sys
from importlib import reload
from datetime import datetime
from datetime import timedelta
from selenium.common.exceptions import WebDriverException
import time

class Queue(object):
    def __init__(self):
        self._queue = []

    def __str__(self):
        return str(self._queue)

    def get_tasks(self):
        return [i for i in self._queue]

    def get_all_job_names(self):
        jobs = []
        for task in self._queue:
            task_name, task_params = task
            if 'jobs' in task_params:
                for job in task_params['jobs']:
                    jobs.append(job[0])
            else:
                jobs.append(task_name)
        return jobs

    def stop(self):
        logging.warning('Queue stopped.')
        self._queue = [('STOP', {})]

    def append(self, value):
        logging.waring('Used deprecated method.')
        return self._queue.append(value)

    def pop(self):
        return self._queue.pop()

    def insert(self, position, value):
        return self._queue.insert(position, value)

    def add(self, value):
        return self.insert(0, value)

    def add_jobs(self, jobs):
        for job in reversed(jobs):
            self.add(job)

    def add_wait(self, wait_time, jobs):
        if isinstance(wait_time, timedelta):
            self.add(('WAIT', {'delta': wait_time, 'jobs': jobs}))
        elif isinstance(wait_time, datetime):
            self.add(('WAIT_FOR', {'datetime': wait_time, 'jobs': jobs}))
        else:
            raise ValueError('Wrong wait time parameter')





class Controller(object):

    def __init__(self, driver, jobs, queue=None):
        self.driver = driver
        if queue is None:
            self.queue = Queue()
        else:
            self.queue = queue
        self.jobs = jobs


    def print_queue(self):
        print('QUEUE:')
        print('#'* 10)
        print(str(self.queue))
        print('#'* 10)

    def next(self):
#        self.print_queue()
        try:
            job, params = self.queue.pop()
        except IndexError:
            self.queue.add(('LOAD_QUEUE', {}))
            return
        if job in self.jobs:
            worker = self.jobs[job]
            while True:
                try:
                    self.queue = worker(self.driver, self.queue, **params)
                    break
                except WebDriverException as e:
                    logging.warning('Cant load page: %s'  %e)
                    time.sleep(100)
                    try:
                        self.jobs['LOGIN'](self.driver, self.queue)
                    except WebDriverException as e2:
                        logging.warning('Cant relogin: %s'  %e2)
                        time.sleep(200)
        else:
            logging.error('Unknown job: %s.' % job)


