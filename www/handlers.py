#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__='wzl'

' url handlers '
from coroweb import *
from models import *
@get('/')
async def index(request):
    # return web.Response(body=b'<h1>Awesome</h1>',content_type='text/html')
    blogs=await Blog.findAll()
    # return {
        # '__template__':'test.html'
    # }
    # users=yield from User.findAll()
    return {
        '__template__':'index.html',
        'blogs':blogs
    }

'''
@get('/api/users')
async def api_get_users(*,page='1'):
	page_index=get_page_index(page)
	num =await User.findNumber('count(id)')
	p=Page(num,page_index)
	if num==0:
		return dict(page=p,users=())
	users = await User.findAll(orderBy='created_at desc',limit=(p.offset,p.limit))
	for u in users:
		u.passwd='******'
	return dict(page=p,users=users)
'''

@get('/api/users')
async def api_get_users():
    users = await User.findAll(orderBy='created_at desc')
    for u in users:
        u.passwd = '******'
    return dict(users=users)



