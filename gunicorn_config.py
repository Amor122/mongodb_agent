# gunicorn_config.py
"""only example"""
bind = "0.0.0.0:8000"

workers = 4

worker_class = "uvicorn.workers.UvicornWorker"

loglevel = "info"

accesslog = "./logs/gunicorn-access.log"
errorlog = "./logs/gunicorn-error.log"

proc_name = "my_fastapi_app"