import sys

from runtime import *
from helper import *

import os

PORT = os.getenv('CRAFT_DEMO_SAC_PORT', '8082')

def main():
    print "Starting the sac demo..."
    # Start the application server which communicates with runtime server
    server = WSGIServer(('0.0.0.0', int(PORT)), app, handler_class=geventwebsocket.handler.WebSocketHandler)
    server.serve_forever()

if __name__ == '__main__':
    main()
