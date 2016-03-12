# RPiHTTPServer

HTTP server eand request handler built on top of Python standard library's 
BaseHTTPServer.
Originally intended for Raspberry Pi projects with a web interface, the small 
web server and associated request handler add some interesting features to 
BaseHTTPServer and can be used independently of Raspberry Pi

Features:
- config in json file
- optional multithreaded server
- static file serving with cache
- POST parsing
- QS parsing
- dynamic routing based on configuration or convention