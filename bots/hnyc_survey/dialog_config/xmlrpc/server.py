from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import argparse
from ..answer.sentence import distance

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='xmlrpc server wrapper.')
    parser.add_argument('port', nargs='?', default=8000, type=int, help='server port')
    args = parser.parse_args()
    
    with SimpleXMLRPCServer(('localhost', args.port), requestHandler=RequestHandler) as server:
        server.register_introspection_functions()
        server.register_function(distance)
        print(f"SimpleXMLRPC Serving on http://localhost:{args.port}")
        # Run the server's main loop
        server.serve_forever()