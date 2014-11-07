try:
    from gevent.pool import Pool
    from gevent import monkey as curious_george
except ImportError:
    raise RuntimeError('Gevent is required to run a WebhookApplication worker.')

curious_george.patch_all(thread=False, select=False)

import os
import sys
import time
import logging
import signal
import argparse
import ConfigParser
from sharq_webhooks import WebhookApplication


SIGNAL_NAMES = dict((getattr(signal, n), n) \
    for n in dir(signal) if n.startswith('SIG') and '_' not in n )

parser = argparse.ArgumentParser(description='Sharq Webhook Application')
parser.add_argument('-c', '--config', action='store', required=True,
                    help='Absolute path of the configuration file.',
                    dest='config_file')
args = parser.parse_args()
config = ConfigParser.SafeConfigParser()
config_file = os.path.abspath(args.config_file)
config.read(config_file)

log_level = config.get('logging', 'level').upper()
logging.basicConfig(filename=config.get('logging', 'file'), level=log_level)
logging.getLogger("requests").setLevel(log_level)

app = WebhookApplication(config._sections)
pool = Pool(int(config.get('webhooks', 'workers')))

def graceful_exit(signal_number, current_stack_frame):
    print "Received signal %s" % SIGNAL_NAMES[signal_number]
    print "Shutting down gevent pool..."
    start = time.clock()
    pool.kill(block=True)
    print "Shutdown complete in %d ms" % ((time.clock()-start) * 1000)
    sys.exit(0);

for sig in [signal.SIGINT, signal.SIGQUIT, signal.SIGTERM]:
    signal.signal(sig, graceful_exit)

app.run(pool=pool)
