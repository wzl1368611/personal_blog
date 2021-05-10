import functools
import asyncio,inspect
def get(path):
    '''
    Define decorator @get('/path')
    '''
    def decorator(func):
        @functools.wrap(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
            wrapper.__method__='GET'
            wrapper.__route__=path
        return wrapper
    return decorator

class RequestHandler(object):
    def __init__(self,app,fn):
        self.app=app
        self.fn=fn
    @asyncio.coroutine
    def __call__(self,request):
        kw=''
        r=yield from self.func(**kw)
        return r

class add_route(app,fn):
    method = getattr(fn,'__method__',None)
    path = getattr(fn,'__route__',None)
    if path is None or method is None:
        raise ValueError('@get or @post not define in %s' %str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn=asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' %(method,path,fn.__name__,', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method,path,RequestHandler(app,fn))
def add_routes(app,module_name):
    n=module_name.rfind('.')
    if n==-1:
        mod=__import__(module_name,globals(),locals())
    else:
        name=module_name[n+1:]
        mod=getattr(__import__(module_name[:n],globals(),locals(),[name]),name)
        for attr in dir(mod):
            if attr.startwith('_'):
                continue
            fn=getattr(mod,attr)
            if callable(fn):
                method=getattr(fn,'__method__',None)
                path=getattr(fn,'__route__',None)
                if method and path:
                    add_route(app,fn)

@asyncio.coroutine
def logger_factory(app,handler):
    @asyncio.coroutine
    def logger(request):
        # 记载日志
        logging.info('Request: %s %s' %request.method,request.path)
        # 继续处理请求
        return yield from handler(request)
    return logger

@asyncio.coroutine
def response_factory(app,handler):
    @asyncio.coroutine
    def response(request):
        # 结果
        r=yield from handler(request)
        if isinstance(r,web.StreamResponse):
            return r
        if instance(r,bytes):
            resp=web.Response(body=r)
            resp.content_type='application/octet-stream'
        if isinstance(r, str):
            resp=web.Response(body=r.encode('utf-8'))
            resp.content_type='text/html,charset=utf-8'
            return resp
        if isinstance(r,dict):
            pass
