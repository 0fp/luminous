#!/usr/bin/env python3.4
import http.server
import socketserver

PORT = 8007

Handler = http.server.CGIHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)
httpd.server_name = "luminousd"
httpd.server_port = PORT

print ("serving at port", PORT)
httpd.serve_forever()
