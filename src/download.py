import argparse
import os.path
import queue
import sys
import threading
from os.path import exists

from tqdm import tqdm

from src.loader import Loader


class Work:
    def __init__(self, file: str):
        self.file = file
        self.wait_queue = queue.Queue(maxsize=1)

    def done(self):
        return self.wait_queue.put(self, block=False)

    def wait(self):
        return self.wait_queue.get()

    def do(self, loader: Loader, dir):
        try:
            file = os.path.join(dir, self.file + ".xml")
            if exists(file):
                file_stats = os.stat(file)
                if file_stats and file_stats.st_size > 0:
                    return
            str = loader.get_one(self.file)
            with open(file, "w") as f:
                f.write(str)
        finally:
            self.done()


def main(argv):
    parser = argparse.ArgumentParser(description="Download documents from teistai.lr service",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--url", nargs='?', required=True, help="Service URL")
    parser.add_argument("--out_dir", nargs='?', required=True, help="Output directory")
    parser.add_argument("--user", nargs='?', required=True, help="User")
    parser.add_argument("--password", nargs='?', required=True, help="Pass")
    parser.add_argument("--domain", nargs='?', required=True, help="Domain")
    parser.add_argument("--n", type=int, nargs='?', default=1, help="Workers count")
    args = parser.parse_args(args=argv)

    loader = Loader(args.url, user=args.user, domain=args.domain, password=args.password)

    ids = loader.get_list()
    print(ids)

    jobs = []
    for id in ids:
        jobs.append(Work(id))

    job_queue = queue.Queue(maxsize=10)
    workers = []
    wc = 1

    def add_jobs():
        for _j in jobs:
            job_queue.put(_j)
        for _i in range(wc):
            job_queue.put(None)

    def start_thread(method):
        thread = threading.Thread(target=method, daemon=True)
        thread.start()
        workers.append(thread)

    start_thread(add_jobs)

    def start():
        while True:
            _j = job_queue.get()
            if _j is None:
                return
            _j.do(loader, args.out_dir)

    for i in range(wc):
        start_thread(start)

    with tqdm("downloading", total=len(jobs)) as pbar:
        for i, j in enumerate(jobs):
            j.wait()
            pbar.update(1)
    for w in workers:
        w.join()


if __name__ == "__main__":
    main(sys.argv[1:])
