# RPiHTTPServer

HTTP server and request handler built on top of Python standard library's
BaseHTTPServer.
Originally intended for Raspberry Pi projects with a web interface, the small
web server and the associated request handler add some interesting features to
BaseHTTPServer and can be used independently of Raspberry Pi.

The provided example shows how to create a simple web interface to switch
ON / OFF a LED via Raspberry GPIO.

## Features:

- config in json file
- optional multithreaded server
- static file serving with cache
- POST parsing
- QS parsing
- dynamic routing based on configuration or convention

## Basic usage:

If you are familiar with Python standard library's BaseHTTPServer and
BaseHTTPRequestHandler it should be pretty straightforward: add a method named
`routed_<request>` to your handler class in order to handle a request for the
`/<request>` URL and set the `self.content` property to the HTML string to be
served over HTTP.

```python
class MyHandler(RPiHTTPRequestHandler):
  def routed_whatever:
  # your method definition to serve http://<my_address>:<my_port>/whatever
    # do cool stuff
    self.content = "<html><body>whatever</body></html>"

MyServer = RPiHTTPServer(path_to_config_file, MyHandler)
MyServer.serve_forever()
```

## Default config:

```json
{
  "SERVER_ADDRESS": "0.0.0.0",
  "SERVER_PORT": 8000,
  "SERVER_MULTITHREADED": true,
  "STATIC_URL_PREFIX": "/static",
  "STATIC_FOLDER":  "$CWD/static",
  "STATIC_CACHE": 604800,
  "TEMPLATE_FOLDER": "$CWD/templates",
  "ROUTE": {
    "GET": {
      "": "default_response",
    },
    "POST": {
      "": "default_response",
    }
  }
}
```

## Detailed instructions

### Configuration file

Prepare your config file in JSON format following the format of the aforementioned
default config.
Any missing key will be replaced by the default (e.g.: if you do not specify the
port the server will try to start listening on port 80).

Add whatever configuration additional parameter you may need, for instance
`"GPIO_PIN": 5`.

Leave "ROUTE" like it is for the time being (read more about routes below).

### Static files

If you want to be able to serve static content, such as images, css, fonts,
javascripts, etc., prepare a folder for such files and put the absolute path in
the config parameter "STATIC_FOLDER".

You can serve static content directly from a subdir named "static" under the
directory where your python script is: in such case, just omit the
"STATIC_FOLDER" parameter in the config file.

The config parameter "STATIC_URL_PREFIX" identifies the virtual path to be
prepended in the URL to reach static files from HTTP. So, for instance, if you
leave the default "STATIC_URL_PREFIX" and you have an image named "foo.png"
directly under the configured "STATIC_FOLDER", this will be served via HTTP
under

  http://<your_server_address>:<your_port>/static/foo.png

### Python script

Now in your Python script you need to define the logic by extending the
RPiHTTPRequestHandler class.
By default every request to the HTTP server is mapped to a method of the
extended class with the same name of the request prepended by `routed_`.

For instance, a request to `http://<your_server_address>:<your_port>/switchon`,
will look for the method `routed_switchon` of the request handler class. If the
method is not available the server will simply give a 404 error.

If you want to specify a custom method for a request, define the method in the
"ROUTE" config parameter. One method you would like almost certainly define (or
override) is the `default_response` (request for the ""/"" URL).

The mapped method just need to set the `self.content` variable (as a string) and
such content will be served over HTTP with content type `text/html; charset=UTF-8`
(the default mime type).

In such scenario, your code could look like this:

```python
class MyHandler(RPiHTTPRequestHandler):

  def routed_switchon(self):
    # DO something cool, e.g.: GPIO.output(self.config.GPIO_PIN, GPIO.HIGH)
    self.content = "<!DOCTYPE html><html><h1>Switch on</h1></html>"

  def routed_switchoff(self):
    # DO something cool, e.g.: GPIO.output(self.config.GPIO_PIN, GPIO.LOW)
    self.content = "<!DOCTYPE html><html><h1>Switch off</h1></html>"

MyServer = RPiHTTPServer("/path/to/config.json", MyHandler)
MyServer.serve_forever()
```

From the example above it should be clear that you can have access to the config
parameters via `self.config.PARAMETER_NAME`.
You can also add additional properties to the `server` property of the
RPiHTTPServer instance, thus making them available in the request handler class
via `self.server.PROPERTY_NAME`. So for instance, referring to the example above
you could write:

```python
MyServer = RPiHTTPServer("/path/to/config.json", MyHandler)
MyServer.server.switch_status = 0
MyServer.serve_forever()
```
Now in MyHandler you can access to `switch_status` via `self.server.switch_status`.

Other properties you can specify/alter before setting `self.content`:

- `self.content_type`: by default set to "text/html; charset=UTF-8"
- `self.response_status`: integer, by default set to 200
- `self.response_headers`: by default an empty dictionary, it will be
automatically filled with Content-Type and Content-Length before sending the
response back to the client. Set additional dictionary keys to serve additional
headers.

Other useful properties accessible in the request handler class:

- `self.config`: gives you access to the configuration
- `self.url`: urlparse result on the request path
(see https://docs.python.org/2/library/urlparse.html)
- `self.qs`: dictionary containing the parameters of the parsed query string
urlparse.parse_qs
- `self.form`: cgi.FieldStorage containing the parameters of the parsed POST
request
(see https://docs.python.org/2/library/cgi.html#higher-level-interface)
- `self.request_xhr`: boolean set to true if the request was issued via xhr

At the current stage the library does not offer support for parametric routes.

### HTML templates

The library does only offer a very basic template handling. The method
`render_template` of the RPiHTTPRequestHandler class expects a filename and a
dictionary and set the content to a string. It will look for a file with the
specified filename under the folder `self.config.TEMPLATE_FOLDER` (if not
specified in the config file it will default to a folder named "templates" under
the directory from which the python script is run). It will then loop the
dictionary's keys as the strings to be replaced, and the corresponding values as
the replacements. Finally, it will set the content property to the resulting
string.

This is an extremely simple and inefficient template's handling: there are many
better libraries out there (e.g. Jinja2, Pystache) if you want a better template
handling: at the end of the day you have to set the `self.content` variable to
the string that will be served over HTTP (to serve a default text/html
  content-type).

Please note that UTF-8 will be served by default and currently I don't plan to
offer any other charset support.

## TODO

- support for Python 3k
- handle config file parse error
- parametric routes
- sanitize path in url request
- handle file upload
- safely handle non utf-8 chars in POST request
