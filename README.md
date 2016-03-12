# RPiHTTPServer

HTTP server and request handler built on top of Python standard library's 
BaseHTTPServer.
Originally intended for Raspberry Pi projects with a web interface, the small 
web server and associated request handler add some interesting features to 
BaseHTTPServer and can be used independently of Raspberry Pi

## Features:
- config in json file
- optional multithreaded server
- static file serving with cache
- POST parsing
- QS parsing
- dynamic routing based on configuration or convention

## Usage:

    class MyHandler(RPiHTTPRequestHandler):
      # your class definition
      ...

    MyServer = RPiHTTPServer(path_to_config_file, MyHandler)
    MyServer.serve_forever()

## Default config:

		{
	    "SERVER_ADDRESS": "0.0.0.0",
	    "SERVER_PORT": 80,
	    "SERVER_MULTITHREADED": True,
	    "STATIC_URL_PREFIX": '/static', 
	    "STATIC_FOLDER": os.getcwd(), # take cwd as default
	    "STATIC_CACHE": 604800,
	    "ROUTE": { # basic dynamic routing
	      "GET": {
	        "": "default_response",
	      },
	      "POST": {
	        "": "default_response",
	      }
	    }
	  }

