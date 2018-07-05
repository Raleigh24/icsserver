import pickle
import network
import resource


class RPCHandler:
    def __init__(self):
        self._functions = {}

    def register_function(self, func):
        self._functions[func.__name__] = func

    def run_rpc(self, pickled_rpc):
        func_name, args, kwargs = pickle.loads(pickled_rpc)
        try:
            try:
                result = self._functions[func_name](*args, **kwargs)
                return pickle.dumps(result)
            except Exception as e:
                #ex_type, ex, tb = sys.exc_info()
                #logging.debug(traceback.print_tb(tb))
                return pickle.dumps(e)
        except EOFError:
            pass


class RPCProxy:
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


rpc_function_list = [
    resource.res_online,
    resource.res_offline,
    resource.res_add,
    resource.res_delete,
    resource.res_state,
    resource.res_clear,
    resource.res_probe,
    resource.res_dep,
    resource.res_list,
    resource.res_link,
    resource.res_unlink,
    resource.res_value,
    resource.res_modify,
    resource.res_attr,
    resource.grp_online,
    resource.grp_offline,
    resource.grp_add,
    resource.grp_delete,
    resource.grp_enable,
    resource.grp_disable,
    resource.grp_state,
    resource.grp_flush,
    resource.grp_clear,
    resource.grp_resources,
    resource.grp_list
]


def rpc_runner():
    rpc_handler = RPCHandler()
    for func in rpc_function_list:
        rpc_handler.register_function(func)

    while True:
        fd, pickled_rpc = network.recv_queue.get()
        result = rpc_handler.run_rpc(pickled_rpc)
        network.send_client_msg(fd, result)






