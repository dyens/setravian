class Stop(object):

    @staticmethod
    def stop(driver, queue, **params):
        queue.add(('STOP', {}))
        return queue
