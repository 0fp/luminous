#!/usr/bin/env python3.4
import http.server
import socketserver

PORT = 8007

Handler = http.server.CGIHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)
#http.cgi_directories = ['/home/ich']
httpd.server_name = "lightserver"
httpd.server_port = PORT

print ("serving at port", PORT)
httpd.serve_forever()
