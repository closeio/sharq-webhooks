import json
import time
import logging
import requests
import traceback


class WebhookApplication(object):
    def __init__(self, config):
        """ 
        @Warning requests are retried indefinitely.  This may change based on http://github.com/plivo/sharq/issues/1
        """
        self.config = config
        self.session = requests.Session()
        self.session.mount('', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=100, max_retries=0, pool_block=False))
        self.sharq_server = "http%s://%s:%s" % ('s' if self.config['sharq-server']['ssl'] == 'True' else '',
                                                self.config['sharq-server']['host'],
                                                self.config['sharq-server']['port'])
        self.log = logging.getLogger(self.__class__.__name__)

    def enqueue(self, queue_id, job_id, interval, requeue_limit, payload):
        request_data = {
            'job_id': job_id,
            'interval': interval,
            'requeue_limit': requeue_limit,
            'payload': payload,
        }
        try:
            response = self.session.post('%s/enqueue/%s/%s/' % (self.sharq_server, self.config['webhooks']['queue_type'], queue_id),
                                    data=json.dumps(request_data), 
                                    headers={'Conent-Type': 'application/json'})
            if response.status_code == 201:
                response_data = response.json()
                if response_data['status'] == 'queued':
                    self.log.info("Enqueued job_id %s", job_id)
                    return True
        except Exception:
            self.log.error(traceback.format_exc())
        self.log.error("Enqueue failed for job_id %s", job_id)
        return False

    def dequeue(self):
        try:
            response = self.session.get('%s/dequeue/%s/' % (self.sharq_server, self.config['webhooks']['queue_type']))
            if response.status_code == 200:
                response_data = response.json()
                if response_data['status'] == 'success':
                    self.log.info("Dequeued job_id %s", response_data['job_id'])
                    return (True, response_data)
        except Exception:
            self.log.error(traceback.format_exc())
        return (False, None)

    def finish(self, queue_id, job_id):
        try:
            response = self.session.post('%s/finish/%s/%s/%s/' % (self.sharq_server, self.config['webhooks']['queue_type'], queue_id, job_id))
            if response.status_code == 200:
                response_data = response.json()
                if response_data['status'] == 'success':
                    self.log.info("Finished job_id %s", job_id)
                    return True
        except Exception:
            self.log.error(traceback.format_exc())
        self.log.error("Finish failed for job_id %s", job_id)
        return False

    def process(self, message):
        queue_id = message['queue_id']
        job_id = message['job_id']
        payload = message['payload']

        headers = payload['headers']
        url = payload['url']
        data = payload['data']

        response = self.session.post(url, data=data, headers=headers)
        if response.status_code == 200:
            self.finish(queue_id, job_id)

    def run(self, pool=None):
        self.log.info("%s worker started with a greenlet pool size of %d using sharq-server %s", __name__, pool.size, self.sharq_server)

        while True:
            try:
                success, message = self.dequeue()
                if success:
                    pool.spawn(self.process, message)
                else:
                    time.sleep(1)
            except Exception:
                self.log.error(traceback.format_exc())
