import click
import logging
import json
import os
import pprint
import time
from termcolor import colored

logger = logging.getLogger()

log = lambda *x,**xx:logger.info(*x, **xx)

from dqueue import from_uri
from dqueue.core import Queue, Task
from dqueue.proxy import QueueProxy

@click.group()
@click.option("-q", "--quiet", default=False, is_flag=True)
@click.option("-d", "--debug", default=False, is_flag=True)
@click.option("-q", "--queue", default=None)
@click.pass_obj
def cli(obj, quiet=False, debug=False, queue=None):
    if quiet:
        logging.basicConfig(level=logging.CRITICAL)
    else:
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    if queue is None:
        queue = os.environ.get('DQUEUE_LEADER', None)

    obj['queue'] = from_uri(queue)
    logger.info("using queue: %s", obj['queue'])

@cli.command()
@click.pass_obj
def info(obj):
    for q in obj['queue'].list_queues(None):
        log(colored(q, 'green'))
        for k,v in q.info.items():
            print(k, ":", len(v), end="; ")
        print("\n")
        #log(q.list(kinds=["waiting","done","failed","running"]))
        #print(q.show())

@cli.command()
@click.pass_obj
def purge(obj):
    if True:
        obj['queue'].purge()
    else:
        for q in Queue().list_queues():
            log(q.info)
            log(q.list_task(kinds=["waiting","done","failed","running"]))
            q.purge()

def console_size():
    try:
        return [int(i) for i in os.popen('stty size', 'r').read().split()]
    except Exception as e:
        logger.warning("problem getting console size: %s", e)
        return 40, 200

@cli.command("ls")
@click.option("-d", "--debug", default=False, is_flag=True)
@click.option("-l", "--log", default=False, is_flag=True)
@click.option("-i", "--info", default=False, is_flag=True)
@click.pass_obj
def list(obj, debug, log, info):
    for task in obj['queue'].list_tasks():

        td = task['task_dict']['task_data']


        s = [colored(task['key'], "red"), task['queue'], colored(task['state'], 'blue')]

        s.append(task['created'])

        if 'object_identity' in td:
            oi = td['object_identity']

            if 'full_name' in oi:
                s.append( colored(oi['full_name'], "yellow"))
            elif 'name' in oi:
                s.append( colored(oi['name'], "yellow"))

        if info:
            ti = obj['queue'].task_info(task['key'])
            print(ti['task_info']['task_data']['object_identity']['factory_name'] )#['task_dict'])


        s.append(repr(td))


        cut_width = console_size()[1]
        m = " ".join(s)

        print(m[:cut_width], end="")
        if len(m) > cut_width:
            print(colored(f"...{len(m)-cut_width} more", "blue"))
        else:
            print("")

        if debug:
            print(pprint.pformat(task))
            t = Task.from_task_dict(task['task_dict'])
            print("Task: ", t)
            print("Task key: ", t.key)

        if log:
            for l in obj['queue'].view_log(task['key'])['event_log']:
                print("  {timestamp} {message}".format(**l))

        #print('task_id', task['task_id'])
    
@cli.command()
@click.pass_obj
@click.argument("key")
@click.option("--follow", "-f", is_flag=True, default=False)
def viewtask(obj, key, follow):
    ti = obj['queue'].task_info(key)

    print(json.dumps(ti))

@cli.group("log")
def logcli():
    pass

@logcli.command()
@click.pass_obj
@click.option("--follow", "-f", is_flag=True, default=False)
@click.option("--since", "-s", default=0)
def view(obj, follow, since=0):
    waiting = False

    info_cadence = 10
    till_next_info = info_cadence

    task_info_cache={}

    while True:
        new_messages = obj['queue'].view_log(since=since)['event_log']


        for l in new_messages:
            logging.debug(l)

            if waiting:
                print("")
                waiting=False

            if l['task_key'] not in task_info_cache:
                ti = obj['queue'].task_by_key(l['task_key'], decode=True)
                task_info_cache[l['task_key']] = ti


            ti = task_info_cache[l['task_key']]

            logger.debug(ti)

            if ti is not None:
                try:
                    name = ti['task_dict']['task_data']['object_identity']['factory_name']
                except Exception as e:
                    logger.error("very stange task: %s; %s", ti.keys(), e)
                    name = "unnamed"
            else:
                name = "unnamed"

            print(("{since} {timestamp} "+colored("{task_key:10s}", "red") + " {message:40s} "+colored("{name:20s}", "yellow") + colored(" {worker_id:40s}", "blue") ).format(
                    since=since,
                    name=name,
                    **l))

            logger.debug(l)
            

            since = l['id']+1

        if not follow:
            break

        if len(new_messages)==0:
            if not waiting:
                print("waiting", end="")
            else:
                print(".", end="", flush=True)

            waiting = True

            till_next_info -= 1

            if till_next_info <=0:
                print()
                for k,v in obj['queue'].info.items():
                    print(k, ":", len(v), end="; ")
                print()

                till_next_info = info_cadence


        time.sleep(1) # nobody ever needs anything but this default

    print("")

@logcli.command()
@click.pass_obj
@click.option("--before", "-b", default=None, type=float)
@click.option("--kind", "-k", default=None, type=str)
def clear(obj, before, kind):
     N = obj['queue'].clear_event_log(before, kind)
     print("cleared", N)

###

@cli.group("data")
def datacli():
    pass

@datacli.command("assert")
@click.pass_obj
@click.option("-g", "--dag", type=click.File('rt'))
@click.option("-d", "--data", type=click.File('rt'))
def assert_fact(obj, dag, data):
    dag = json.load(dag)
    data = json.load(data)

    obj['queue'].assert_fact(
                dag=dag,
                data=data,
            )

@datacli.command()
@click.pass_obj
@click.option("-g", "--dag", type=click.File('rt'))
def consult(obj, dag):
    dag = json.load(dag)

    obj['queue'].consult_fact(dag=dag)
    

@datacli.command()
@click.pass_obj
def list_facts(obj):
    pass

###

@cli.command()
@click.option('-w', '--watch', default=None, type=int)
@click.pass_obj
def guardian(obj, watch):
    while True:
        #try_all_locked
        print("trying to unlock something")
        task_data=obj['queue'].try_all_locked()
        print(colored("unlocked:", "green"), task_data)
        
        #clear event log 
        N = obj['queue'].clear_event_log(only_older_than_days=2./24.)
        print(f"cleared event log of {N} entries")

        # stats

        print("getting queue statistics...")
        for k,v in obj['queue'].info.items():
            print(k, ":", len(v), end="; ")
        print("\n")

        print("sleeping", watch)

        if not watch:
            break
        time.sleep(watch)

@cli.command()
@click.pass_obj
def get(obj):
    task_data=obj['queue'].get()
    print(colored("offered:", "green"), task_data)

@cli.command()
@click.argument("task_data")
@click.pass_obj
def question(obj, task_data):
    j_task_data=json.loads(task_data)
    r = obj['queue'].put(j_task_data)
    print(colored("questioned:", "green"), task_data, ":", r)

@cli.command()
@click.option('-s', '--scope-selector', default="state:all")
@click.pass_obj
def resubmit(obj, scope_selector):
    scope, selector = scope_selector.split(":")

    r = obj['queue'].resubmit(scope, selector).response().result
    print(colored("resubmitted:", "green"), ":", r)


def main():
    cli(obj={})

if __name__ == "__main__":
    main()

