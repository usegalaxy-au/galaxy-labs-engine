"""Run a local server for build purposes."""

import sys
import subprocess
import time

import requests
from django.conf import settings


class Runserver:
    """Run Django development server to be queried by ElasticSearch."""

    ARGS = (
        sys.executable,
        'manage.py',
        'runserver',
        settings.HOSTNAME,
    )

    def __init__(self, delay_seconds=0):
        self.delay_seconds = delay_seconds
        try:
            self.server = subprocess.Popen(
                self.ARGS,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as exc:
            print(exc)
            raise RuntimeError(
                'Could not run Django development server'
                ' - check errors above.')

    def __enter__(self):
        time.sleep(self.delay_seconds)
        self.await_server()
        return self

    def await_server(self):
        server_url = f'http://{settings.HOSTNAME}'
        print(
            f'Waiting for server at {server_url} to come online',
            end='', flush=True)
        while True:
            try:
                response = requests.get(server_url)
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                pass
            print('.', end='', flush=True)
            time.sleep(1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.server.terminate()

    def terminate(self):
        if self.server.poll() is not None:
            stdout, stderr = self.server.communicate()
            if self.server.returncode:
                print(f'\nDjango development server exited with code'
                      f' {self.server.returncode}')
                print("\nServer stderr:")
                print(stderr.decode('utf-8'))
        self.server.terminate()
