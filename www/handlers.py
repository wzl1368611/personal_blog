#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__='wzl'

' url handlers '
from coroweb import *
from models import *
@get('/')
async def index(request):
    # return web.Response(body=b'<h1>Awesome</h1>',content_type='text/html')
    users=await User.findAll()
    # return {
        # '__template__':'test.html'
    # }
    # users=yield from User.findAll()
    return {
        '__template__':'test.html',
        'users':users
    }
