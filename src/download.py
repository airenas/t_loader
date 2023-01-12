import argparse
import os.path
import queue
import sys
import threading
from os.path import exists

from tqdm import tqdm

from src.loader import Loader, Cfg


class Work:
    def __init__(self, file: str):
        self.file = file
        self.wait_queue = queue.Queue(maxsize=1)
        self.err = 0

    def done(self):
        return self.wait_queue.put(self, block=False)

    def wait(self):
        return self.wait_queue.get()

    def do(self, loader: Loader, dir):
        try:
            n_dir = os.path.join(dir, self.file[0])
            if not exists(n_dir):
                os.makedirs(n_dir, exist_ok=True)
            file = os.path.join(n_dir, self.file + ".xml")
            if exists(file):
                file_stats = os.stat(file)
                if file_stats and file_stats.st_size > 0:
                    return True
            str = loader.get_one(self.file)
            with open(file, "w") as f:
                f.write(str)
        except BaseException as err:
            print("error {}".format(err))
            self.err += 1
            return False
        finally:
            self.done()
        return True


def main(argv):
    parser = argparse.ArgumentParser(description="Download documents from teistai.lr service",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--url", nargs='?', required=True, help="Service URL")
    parser.add_argument("--out_dir", nargs='?', required=True, help="Output directory")
    parser.add_argument("--court", nargs='?', required=True, help="Court ID")
    parser.add_argument("--user", nargs='?', required=True, help="User")
    parser.add_argument("--password", nargs='?', required=True, help="Pass")
    parser.add_argument("--domain", nargs='?', required=True, help="Domain")
    parser.add_argument("--n", type=int, nargs='?', default=1, help="Workers count")
    parser.add_argument("--top", type=int, nargs='?', default=0, help="Take top n docs for each court")
    args = parser.parse_args(args=argv)

    cfg = Cfg(args.url, user=args.user, domain=args.domain, password=args.password)

    print("court ID: %s" % args.court)
    print("loading ids...")
    ids = get_or_load_ids(Loader(cfg=cfg), args.out_dir, args.court)
    print("got %d docs ids" % len(ids))
    if args.top > 0:
        print("take top %d docs of %d" % (args.top, len(ids)))
        ids = ids[:args.top]
    print("out dir: %s" % args.out_dir)
    print("worker count: %d" % args.n)
    jobs = []
    for id in ids:
        jobs.append(Work(id))

    job_queue = queue.Queue(maxsize=10)
    workers = []
    wc = args.n

    def add_jobs():
        for _j in jobs:
            job_queue.put(_j)
        for _i in range(wc):
            job_queue.put(None)

    def start_thread(method, add: bool = True):
        thread = threading.Thread(target=method, daemon=True)
        thread.start()
        if add:
            workers.append(thread)

    start_thread(add_jobs, add=False)

    err_lock = threading.Lock()
    err_count = 0

    def start():
        nonlocal err_count
        while True:
            _j = job_queue.get()
            if _j is None:
                return
            if not _j.do(Loader(cfg=cfg), os.path.join(args.out_dir, "corpus", args.court)):
                with err_lock:
                    err_count += 1
            if _j.err > 3:
                print("too many errors exit worker")
                break

    for i in range(wc):
        start_thread(start)

    def work():
        with tqdm("downloading", total=len(jobs)) as pbar:
            for i, j in enumerate(jobs):
                j.wait()
                pbar.update(1)

    start_thread(work, add=False)

    for w in workers:
        w.join()
    with err_lock:
        print("bye with errs {}".format(err_count))
        if err_count > 0:
            exit(1)


def get_or_load_ids(loader: Loader, dir, court):
    n_dir = os.path.join(dir, "ids")
    if not exists(n_dir):
        os.makedirs(n_dir, exist_ok=True)
    file = os.path.join(n_dir, court + ".txt")
    if exists(file):
        print("File exists: {}".format(file))
        with open(file, "r") as f:
            return [line.rstrip() for line in f]
    res = loader.get_list(court)
    with open(file, "w") as f:
        f.write("\n".join(res))
    print("Wrote file: {}".format(file))
    return res


if __name__ == "__main__":
    main(sys.argv[1:])
