import orm
from models import User,Blog,Comment
import asyncio
def test(loop):
    yield from orm.create_pool(loop,user='www-data',password='www-data',database='awesome')
    u=User(name='Test',admin=True,email='1793268783@qq.com',passwd='1234567890',image='about:blank')
    yield from u.save()
# for x in test():
#   pass
loop=asyncio.get_event_loop()
loop.run_until_complete(test(loop))
# loop.run_forever()
