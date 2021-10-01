from locust import HttpUser, TaskSet, task, events, web
import socket, atexit, locust, time, logging

class GraphanaPlugin():
    sock = None
    request_success_stats = [list()]
    request_fail_stats = [list()]

    def __init__(
            self,
            env: locust.env.Environment,
    ):
        self.sock = socket.socket()
        self.sock.connect( ("localhost", 2003) )

        self.env = env
        self.errors = []

        events = self.env.events
        events.request_success.add_listener(self.hook_request_success)
        events.request_failure.add_listener(self.hook_request_fail)
        atexit.register(self.exit_handler)
        events.quitting.add_listener(self.exit_handler)

    def hook_request_success(self, name, response_time, **_kwargs):
        message = "%s %d %d\n" % ("performance." + name.replace('.', '-'), response_time,  time.time())
        self.sock.send(message.encode())

    def hook_request_fail(self, request_type, name, response_time, exception, **_kwargs):
        self.request_fail_stats.append([name, request_type, response_time, exception])

    def exit_handler(self, environment):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()