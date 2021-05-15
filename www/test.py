import orm
from models import User,Blog,Comment
import asyncio
def test(loop):
    yield from orm.create_pool(loop,user='root',password='rootpwd',database='awesome')
    u=User(name='Test',admin=True,email='1793268783@qq.com',passwd='1234567890',image='about:blank')
    yield from u.save()
# for x in test():
#   pass
def test_02(loop):
    id='0016209608217112a916d832bfa46de9d76a612de8582ea000'

    pass
loop=asyncio.get_event_loop()
loop.run_until_complete(test(loop))
# loop.run_forever()
