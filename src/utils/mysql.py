import datetime
import os
import collections
import logging

import mysql.connector
import mysql.connector.pooling


class MySQLWrapper(object):
	def __init__(self, db_conf_dict):
		self.db_conf_dict = db_conf_dict
		self.cnx_pool = mysql.connector.pooling.MySQLConnectionPool(pool_size=5, pool_name='pool', **db_conf_dict)
		self.msgs_to_write = collections.deque()
	
	def get_conn(self):
		try:
			conn = self.cnx_pool.get_connection()
			if not conn.is_connected():
				conn.reconnect()
		except:
			try:
				conn = mysql.connector.connect(**self.db_conf_dict)
			except:
				conn = None
				logging.info('can not connect to mysql')
		return conn

	def add_conn_to_pool(self, conn):
		try:
			self.cnx_pool.add_connection(conn)
		except mysql.connector.errors.PoolError:
			pass
	
	def add_user(self, username):
		conn = self.get_conn()
		if not conn:
			return
		cursor = conn.cursor()
		try:
			datetime_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
			cursor.execute("INSERT INTO auth_user "
			                    "(password, last_login, is_superuser, username, first_name, "
			                    "last_name, email, is_staff, is_active, date_joined) "
			                    "VALUES ('pbkdf2_sha256$180000$BRwVYtXmFFp3$H07C47znFJee6a81XH6HCiK5zYEIPS8yAZ4OEkkdxEE=',"
			                    "%s, 0, %s, '', '', '', 1, 1, %s)", (datetime_now, username, datetime_now))
			conn.commit()
		except mysql.connector.errors.IntegrityError as err:
			logging.info('mysql.connector.errors.IntegrityError: %s' % err)
		self.add_conn_to_pool(conn)
		
		
	
	def get_user_id(self, username):
		conn = self.get_conn()
		if not conn:
			return
		cursor = conn.cursor()
		cursor.execute("select id from auth_user where username=%s", (username,))
		users_id = cursor.fetchone()
		self.add_conn_to_pool(conn)
		return users_id[0] if users_id else None
	
	def add_msg(self, user, receipt, msg, asr_record_path=''):
		datetime_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
		self.msgs_to_write.append((datetime_now, user, receipt, msg, asr_record_path))
	
	def write_msgs(self):
		conn = self.get_conn()
		if not conn:
			return
		cursor = conn.cursor()
		while self.msgs_to_write:
			datetime_now, user, receipt, msg, asr_record_path = self.msgs_to_write.popleft()
			user_id = self.get_user_id(user)
			receipt_id = self.get_user_id(receipt)
			asr_record_path = asr_record_path if os.path.splitext(asr_record_path)[-1] in ['.pcm', '.wav'] else None
			try:
				cursor.execute("INSERT INTO core_messagemodel "
				                    "(timestamp, user_id, recipient_id, body, hash, user_record) "
				                    "values (%s, %s, %s, %s, MD5(%s), %s)",
				                    (datetime_now, user_id, receipt_id, msg, msg, asr_record_path))
			except:
				pass
		try:
			conn.commit()
		except:
			pass
		self.add_conn_to_pool(conn)
