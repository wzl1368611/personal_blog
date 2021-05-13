import logging
import aiomysql


import asyncio, os, json, time
from datetime import datetime
from aiohttp import web
from jinja2 import Environment, FileSystemLoader
import orm
from coroweb import *
from handlers import cookie2user, COOKIE_NAME
import functools
import asyncio, inspect


from config import configs
logging.basicConfig(level=logging.INFO)
'''
def index(request):
    return web.Response(body=b'<h1>Awesome</h1>',content_type='text/html')
'''


'''
def get(path):
    
    #Define decorator @get('/path')
    
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

'''


def init_jinja2(app, **kw):
    logging.info('init jinja2 ...')
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload=kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env


@asyncio.coroutine
def logger_factory(app, handler):
    @asyncio.coroutine
    def logger(request):
        # 记载日志
        logging.info('Request: %s %s' % (request.method, request.path))
        # 继续处理请求
        return (yield from handler(request))

    return logger


async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.data = await request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form: %s' % str(request.__data__))
        return (await handler(request))

    return parse_data


async def auth_factory(app, handler):
    async def auth(request):
        logging.info('check user: %s %s' % (request.method, request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user = await cookie2user(cookie_str)
            if user:
                logging.info('set current user: %s' % user.email)
                request.__user__ = user
        if request.path.startswith('/manage/') and (request.__user__ is None or not request.__user__.admin):
            return web.HTTPFound('/signin')
        return await handler(request)

    return auth


async def response_factory(app, handler):
    async def response(request):
        # 结果
        logging.info('Response handler...')

        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp

        if isinstance(r, str):
            if r.startswith('redirect:s'):
                return web.HTTPFound(r[9:])

            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(
                    body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp

        if isinstance(r, int) and 100 <= r < 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and 100 <= t < 600:
                return web.Response(t, str(m))
        # default
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp

    return response


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return r'%s年%s月%s日' % (dt.year, dt.month, dt.day)


'''
async def init():
    app=web.Application()
    app.router.add_route('GET','/',index)
    runner=web.AppRunner(app)
    await runner.setup()
    site=web.TCPSite(runner,'127.0.0.1',9000)
    await site.start()
    # srv=yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    # return srv
    #更改后的代码
    app=web.Application(middlewares=[logger_factory,response_factory]) 
    init_jinja2(app,filters=dict(datetime=datetime_filter))
    add_routes(app,'handlers')
    add_static(app)
'''


async def init(loop):
    await orm.create_pool(loop=loop, host='127.0.0.1', port=3306, user='root', password='rootpwd', database='awesome')
    app = web.Application(middlewares=[logger_factory, auth_factory, response_factory])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)
    # srv =await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 9000)
    await site.start()

    logging.info('server started at http://127.0.0.1:9000...')
    # return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
