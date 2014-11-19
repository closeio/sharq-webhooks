sharq-webhooks
==============
Uses [SharQ](http://sharq.io) to process webhooks asyncronously.

Typical Use-Case
----------------
You have an application that needs to send webhook requests to customers. Use the WebhookApplication().enqueue() operation within your application to queue a webhook task. Run the WebhookApplication client against your SharQ-Server instance and you now have an asyncronous webhook work queue.

Quick-Start
-----------
```
$ sharq-server -c config/server/local.conf
```
```
$ python sharq_webhooks -c config/client/local.py
```
Configuration
-------------
Within the repo we have both `client` and `server` configurations. The `client` in this case is meant for the Webhook Application.  The `server` is used to run a [SharQ-Server](https://github.com/plivo/sharq-server) instance.
```
[sharq-server]
host                : localhost
port                : 7777
ssl                 : False

[webhooks]
queue_type          : webhooks
workers             : 10

[logging]
file                : /tmp/sharq_webhooks.log
level               : debug
```

Message
-------
This is the sharq message structure which is enqueued.
```
{
    'job_id': '1',
    'interval': 1000,
    'payload':{
        'url': 'http://example.com/my_webhook_endpoint/',
        'headers': {
            'Content-Type': 'application/json',
            # ... any valid HTTP headers ...
        },
        'data': "...",
    },
}
```

Retries
--------
Webhook recipients are assumed to return an HTTP 200 upon successful reciept of our webhook requests. All other response status codes will trigger the request to be retried. You can use the globally defined retry limit of your sharq-server or you can set the retry limit on a per-job basis using the `requeue_limit` parameter within your enqueue request.

