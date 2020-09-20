import datetime
import os
import time
import socket
from hashlib import sha224
from collections import defaultdict
import glob
import json
from io import StringIO
import logging
import re
import click
from urllib.parse import urlparse# type: ignore

from dqueue.core import Queue, Empty, Task, CurrentTaskUnfinished
from dqueue.client import APIClient
import dqueue.core as core

from typing import Union
from dqueue import tools

from retrying import retry # type: ignore

import base64


def serialize(d, b64=False):
    if b64:
        return base64.b64encode(json.dumps(d, sort_keys=True).encode()).decode()
    else:
        return json.dumps(d, sort_keys=True)

#TODO: since we do not use minio's native binary store, and encode everything, we overuse space, 50% depending on the data

class DataFacts(APIClient):
    def assert_fact(self, dag, data):
        return self.client.data.assert_fact(
                    worker_id="test_worker",
                    payload=dict(
                        dag_json=serialize(dag),
                        data_json=serialize(data),
                    )
                ).response().result
    
    def consult_fact(self, dag):
        return self.client.data.consult_fact(
                    worker_id="test_worker",
                    payload=dict(
                        dag_json=serialize(dag),
                    )
               ).response().result
