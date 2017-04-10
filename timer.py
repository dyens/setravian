from datetime import datetime
from datetime import timedelta

class Timer(object):


    @staticmethod
    def wait(driver, queue, **params):
        now = datetime.now()
        delta = params['delta']
        jobs = params.get('jobs', [])
        end = now + delta
        queue.add_wait(end, jobs)
        return queue

    @staticmethod
    def wait_for(driver, queue, **params):
        now = datetime.now()
        job_time = params['datetime']
        jobs = params.get('jobs', [])
        if job_time > now:
            queue.add_wait(job_time, jobs)
        else:
            queue.add_jobs(jobs)
        return queue
