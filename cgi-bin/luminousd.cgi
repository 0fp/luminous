#!/usr/bin/env python3.4
# Echo client program
import socket
import sys
import cgi

HOST = 'localhost'    # The remote host
PORT = 50007              # The same port as used by the server

form = cgi.FieldStorage()

print(form)

#if 'led' not in form:
if 'cmd' not in form:
    sys.exit(0)

# I = form['led'].intensity
cmd = form['cmd'].value

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.send(cmd.encode())
    print(cmd.encode())
except ConnectionRefusedError:
    print("Server not running")
finally:
    s.close()

