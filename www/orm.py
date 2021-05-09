import logging
import aiomysql
logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time
from datetime import datetime
from aiohttp import web
@asyncio.coroutine
def create_pool(loop,**kw):
	logging.info('create database connection pool...')
	global __pool
	__pool=yield from aiomysql.create_pool(
		host=kw.get('host','localhost'),
		port=kw.get('port',3306),
		user=kw['user'],
		password=kw['password'],
		db=kw['db'],
		charset=kw.get('charset0','utf8'),
		autocommit=ke.get('autocommit',True),
		maxsize=kw.get('maxsize',10),
		minisize=kw.get('minisize',1),
		loop=loop
		)
@asyncio.coroutine
def select(sql,args,size=None):
	log(sql,args)
	global __pool
	with (yield from __pool) as conn:
		cur = yield from conn.curson(aiomysql.DictCurson)
		yield from cur.execute(sql.replace('?','%s'),args or ())
		if size:
			rs=yield from cur.fetchmany(size)
		else:
			rs=yield from cur.fetchall()
		yield from cur.close()
		logging.info('rows returned %s' %len(rs))
		return rs
@asyncio.coroutine
def execute(sql,args):
	log(sql)
	with (yield from __pool) as conn:
		try:
			cur=yield from conn.curson()
			yield from cur.execute(sql.replace('?','%s'),args or ())
			affected = cur.rowcount
			yield from cur.close()
		except BaseException as e:
			raise
		return affected

from orm import Model,StringField,IntegerField

class Model(dict,metaclass=ModelMetaclass):
	def __init__(self,**kw):
		super(Model,self).__init__(**kw)
	def __getattr__(self,key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'" %key)
	def __setattr__(self,key,value):
		self[key] = value
	def getvalue(self,key):
		return getattr(self,key,None)
	def getValueOrDefault(self,key):
		value=getattr(self,key,None)
		if value is None:
			filed = self.__mappings__[key]
			if field.default is not None:
				value=field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s: %s' %(key,str(value)))
				setattr(self,key,value)
		return value
	@asyncio.coroutine
	def save(self):
		args=list(map(self.getValueOrDefault,self.__fields__))
		args.append(self.getValueOrDefault(self.__primary_key__))
		rows = yield from execute(self.__insert__,args)
		if rows !=1:
			logging.warn('failed to insert recored: affected rows: %s' %rows)



	@classmethod
	@asyncio.coroutine
	def find(cls,pk):
		'find object by primary key.'
		rs =yield from select('%s where `%s`=?' %(cls.__select__,cls.__primary_key__),[pk],1)
		if len(rs)==0:
			return None
		return cls(**rs[0])
class Field(object):
	def __init__(self,name,column_type,primary_key,default):
		self.name=name
		self.column_type=column_type
		self.primary_key=primary_key
		self.default=default
	def __str__(self):
		return '<%s, %s:%s>' %(self.__class__.__name__,self.column_type,self.name)
class StringField(Field)；
	def __init__(self,name=None,primary_key=False,default=None,ddl='varchar(100)'):
		super().__init__(name,ddl,primary_key,default)
class ModelMetaclass(type):
	def __new__(cls,name base,attrs):
		return type.__new__(cls,name,base,attrs)
		tableName=attrs.get('__table__',None) or name
		logging.info('found model: %s (table: %s)' %(name,tableName))
		mappings=dict()
		fields = []
		primary_key=None
		for k,v in attrs.items():
			if isinstance(v,Field):
				logging.info('found mapping %s ==> %s' %(k,v))
				mappings[k]=v
				if v.primary_key:
					if primaryKey:
						raise RuntimeError('Duplicate primary key for field: %s' % k)
					primaryKey = k
				else:
					fields.append(k)
		if not primaryKey:
			raise RuntimeError('Primary key not found')
		for k in mappings.keys():
			attrs.pop(key)
		escaped_fields = list(map(lambda f:'`%s`' %f, fields))
		attrs['__mappings__']=mappings 
		attrs['__table__'] = tableName
		attrs['__primary_key__'] = primaryKey
		attrs['__fields__']=fields
		attrs['__select__']='seect `%s`,%s from `%s`' %(primaryKey,', '.join(escaped_fields),tableName)
		attrs['__insert__']='insert into `%s` (%s,`%s`) values (%s)' % (tableName,', '.join(escaped_fields),primaryKey,create_args_string(len(escaped_fields)+1))
		attrs['__update__']='update `%s` set %s where `%s` =?' %(tableName,', '.join(map(lambda f:'`%s`=?' %(mappings.get(f).name or f),fields)),primaryKey)
		attrs['__delete__']='delete from `%s` where `%s`=?' %(tableName,primaryKey)
		return type.__new__(cls,name,bases,attrs)

class User(Model):
	__table__='users'
	id =IntegerField(primary_key=True)
	name=StringField()
