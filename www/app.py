import logging
import aiomysql
logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time
from datetime import datetime
from aiohttp import web
def index(request):
	return web.Response(body=b'<h1>Awesome</h1>',content_type='text/html')

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
loop=asyncio.get_event_loop()
loop.run_until_complete(init())
loop.run_forever()
