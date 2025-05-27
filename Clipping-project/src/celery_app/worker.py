from .app import app

if __name__ == '__main__':
    app.worker_main([
        'worker',
        '--pool=threads',
        '--concurrency=10',
        '--loglevel=info'
    ])