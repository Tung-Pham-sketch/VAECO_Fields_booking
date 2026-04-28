# Gunicorn config — SQLite requires a single writer process.
# If you ever switch to PostgreSQL you can raise workers to 2-4.
workers = 1
threads = 4        # handle concurrency within the single process
timeout = 60
bind = "0.0.0.0:10000"