import asyncio, inspect, os, logging, functools
from urllib import parse
from aiohttp import web
from apis import APIError


def get(path):
    '''
    Define decorator @get('/path')
    '''

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper

    return decorator


def post(path):
    '''
    define dectorator @post('/path')
    '''

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper

    return decorator


def get_required_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        logging.info('*******************get_required_kw_args: 11111111*********** :%s , %s' % (name, param))
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            logging.info('*******************get_required_kw_args: 2222222*********** :%s' % name)
            args.append(name)
    logging.info('*******************get_required_kw_args: 333333333*********** :%s' % args)
    return tuple(args)


def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)


def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True


def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True


def has_request_arg(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        if found and (
                param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError(
                'request parameter must be the last named parameter in function: %s %s' % (fn.__name__, str(sig)))
    return found


class RequestHandler(object):
    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)

    async def __call__(self, request):
        logging.info('**************request************* : %s %s %s %s' % (request, request.content_type, dict(**request.match_info),request.json()))
        print('&&&&&&&&&&&&&request对象&&&&&&&&&&&&&&： %s' % request.json())
        kw = None
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            if request.method == 'POST':
                if not request.content_type:
                    # 'Missing Content-Type.'
                    logging.info('******************** RequestHandler HTTPBadRequest 1111111**********************')
                    return web.HTTPBadRequest()
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        # 'JSON body must be object.'
                        logging.info('******************** RequestHandler HTTPBadRequest 2222222**********************')

                        return web.HTTPBadRequest()
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    logging.info('******************** RequestHandler HTTPBadRequest 33333333**********************')
                    return web.HTTPBadRequest()
                logging.info('---------post方法返回值----------')
            if request.method == 'GET':

                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        if kw is None:
            kw = dict(**request.match_info)
            logging.info('**************request kw ************* : %s' % kw)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:
                # remove all unnamed kw
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            # check named args
            for k, v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicated arg name in named arg and kw args: %s' % k)
                kw[k] = v
        if self._has_request_arg:
            kw['request'] = request
        # check required kw
        if self._required_kw_args:
            logging.info('******************** RequestHandler HTTPBadRequest 4444444444 '
                         '_required_kw_args **********************: %s ==> %s' % (self._required_kw_args, kw))
            for name in self._required_kw_args:

                if not name in kw:
                    logging.info('******************** RequestHandler HTTPBadRequest 4444444444**********************')
                    return web.HTTPBadRequest()
        logging.info('call with args: %s' % str(kw))
        try:
            r = await self._func(**kw)
            logging.info('-----------r----- %s' % r)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)


def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))


def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info(
        'add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))
    logging.info('-------添加成功--------------')


def add_routes(app, module_name):
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n + 1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)

    logging.info('------dir(mod)-----%s' % dir(mod))
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        logging.info('-----------fn()------ %s' % fn)
        if callable(fn):
            logging.info('---------callable(fn)----- %s' % fn)
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            logging.info('----------method and path-------%s,%s' % (method, path))
            if method and path:
                add_route(app, fn)
