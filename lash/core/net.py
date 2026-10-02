import socket

REQUEST_TIMEOUT = 60


def install_default_timeout():
    socket.setdefaulttimeout(REQUEST_TIMEOUT)
