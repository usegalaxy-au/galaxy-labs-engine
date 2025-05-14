"""Run a local server for build purposes."""

import sys
import subprocess
import time

import requests
from django.conf import settings

WAIT_MAX_SECONDS = 10


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
        tries = 0
        response = None
        while True:
            exception = None
            try:
                response = requests.get(server_url)
                if response.status_code < 400:
                    break
            except requests.ConnectionError as e:
                exception = e
            print('.', end='', flush=True)
            time.sleep(1)
            tries += 1
            if tries > WAIT_MAX_SECONDS:
                if response:
                    print(f'Server {response.status_code} response:',
                          response.text,
                          file=sys.stderr)
                if exception:
                    print(f'Connection error: {exception}', file=sys.stderr)
                raise RuntimeError(
                    'Could not start Django development server'
                    ' - check for errors above?')

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
