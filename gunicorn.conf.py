import multiprocessing
import os

bind = f"localhost:{os.environ['FLASK_PORT']}"
workers = multiprocessing.cpu_count() * 2 + 1
accesslog = "-"
