import pickle
import network
import logging

logger = logging.getLogger(__name__)


# Client interface class
class RPCProxy:
    """Remote interface object for sending rpc function to server"""
    def __init__(self, connection):
        self._conn = connection

    def __getattr__(self, name):
        def do_rpc(*args, **kwargs):
            network.send_msg(self._conn, pickle.dumps((name, args, kwargs)))
            msg = network.recv_msg(self._conn)
            result = pickle.loads(str(msg))
            if isinstance(result, Exception):
                raise result
            return result

        return do_rpc


# Server interface class
class RPCHandler:
    def __init__(self):
        self._functions = {}

    def register_function(self, func):
        self._functions[func.__name__] = func

    def run_rpc(self, pickled_rpc):
        func_name, args, kwargs = pickle.loads(pickled_rpc)
        try:
            try:
                result = self._functions[func_name](*args, **kwargs)  # Run function
                return pickle.dumps(result)
            except Exception as error:
                logger.exception(error)
                #ex_type, ex, tb = sys.exc_info()
                #logging.debug(traceback.print_tb(tb))
                return pickle.dumps(error)
        except EOFError:
            pass


def rpc_runner(function_list):
    """RPC handler function"""
    rpc_handler = RPCHandler()
    for func in function_list:
        rpc_handler.register_function(func)

    while True:
        fd, pickled_rpc = network.recv_queue.get()
        result = rpc_handler.run_rpc(pickled_rpc)
        network.send_client_msg(fd, result)






