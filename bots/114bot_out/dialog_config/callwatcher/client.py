from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from random import random
import logging
from expiringdict import ExpiringDict

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s')
logging.root.setLevel(logging.DEBUG)

DEBUG=True

dialect = "mysql"
driver = "pymysql"
host = "47.93.120.246"
port = "10576"
username = "root"
password = "XkwJp!c3RO!mlMgr"
database = "callcenter"
url = f"{dialect}+{driver}://{username}:{password}@{host}:{port}/{database}"
print(url)
engine = create_engine(url)
engine.connect()

def cti_cdr(list_id):
    sql = f"""
    SELECT dropcause from cti_cdr where memberid = {list_id}
    """
    res = exec_sql(sql).first()
    if not res:
        return None
    logging.debug(f"cti_cdr return {int(res.dropcause)}")
    return int(res.dropcause)
    
def insert_buslist(customer_phone, extend, tenant_id=2, event_id=2520):
    car_no = extend.split("#")[1]
    sql = f"""
    INSERT INTO ocm_buslist (tenant_id , customer_name, customer_phone, event_id, call_number, create_time, car_no, extend, channel_no, templet_id) 
    VALUES (2,'BOT', {customer_phone}, {event_id}, '00000000000', NOW(), '{car_no}', '{extend}', 1, '03')
    """
    sql = sql.replace("\n","")
    res = exec_sql(sql)
    return res.lastrowid

def update_buslit(list_id):
    """
    UPDATE cti_cdr set dropcause=200 where memberid = {list_id};
    """
    
def create_call_result():
    sql = """
    CREATE TABLE `ocm_callout_result` (
      `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
      `callid` bigint(20) NOT NULL COMMENT '对话唯一性id(在cti_cdr中主键)',
      `from_callid` bigint(20) NOT NULL  COMMENT '内呼任务id',
      `content` varchar(1000) DEFAULT NULL COMMENT '机器人内容',
      `extend` varchar(100) DEFAULT NULL COMMENT '扩展字段',
      `call_result` varchar(100) DEFAULT NULL COMMENT '呼叫结果',
      PRIMARY KEY (`id`) USING BTREE
    ) 
    """
    sql = sql.replace("\n","")
    res = exec_sql(sql)
    return res
    
def insert_callout_result(callid, from_callid, content, extend, call_result):
    sql = f"""
    INSERT INTO ocm_callout_result (callid, from_callid, content, extend, call_result) 
    VALUES ({callid}, {from_callid}, '{content}', '{extend}', '{call_result}')
    """
    sql = sql.replace("\n","")
    res = exec_sql(sql)
    return res.lastrowid
    
def bot_result(callid):
    sql = f"""
    SELECT call_result from ocm_callout_result WHERE from_callid = {callid}
    """
    sql = sql.replace("\n","")
    res = exec_sql(sql).first()
    logging.debug(f'bot_result: {res}')
    if not res:
        return 0
    return int(res.call_result)

def last_buslist():
    sql = """
    select list_id, customer_phone, customer_name, car_no, extend from ocm_buslist order by list_id desc limit 5
    """
    res = exec_sql(sql)
    print(res.next())
    
def exec_sql(sql):
    if DEBUG:
        logging.debug(sql.strip())
    res = engine.execute(sql)
    return res

def last_cti_cdr():
    sql = """
    select memberid, dropcause from cti_cdr order by memberid desc limit 5
    """
    res = exec_sql(sql)
    print(res.next())    
        

from enum import Enum
class Response(Enum):
    CONNECTING = "正在尝试第{{{0}}}次联系车主，请您耐心等待"
    RETRY = "车主的电话暂未接通,还将重试{{{0}}}次，请您耐心等待"
    CONNECTED = "我们已经和车主取得联系,正在沟通中"
    FAIL = "十分抱歉，对方车主无人接听，现在无法帮您通知车主挪车"
    ACCEPT_200 = "已通知到车主，车主答应挪车。感谢您的来电，请您挂机"
    REJECT_300 = "车主目前不方便挪车，请您通过其他途径解决。感谢您的来电，请您挂机"
    WRONG_USER_401 = "该车牌号并非车主本人，无法帮您挪车。感谢您的来电，请您挂机"
    WRONG_LOCATION_402 = "车主的车没有停在这个位置，无法帮您挪车。感谢您的来电，请您挂机"
    UNKNOW = "未知的错误代码{0}"
    def render(self, *args):
        return self.value.format(*args)
        
    def is_terminal(self):
        return self in [Response.FAIL, Response.ACCEPT_200, Response.REJECT_300, Response.WRONG_USER_401, Response.WRONG_LOCATION_402, Response.UNKNOW]
    
class CallidSingleton(type):
    
    def __init__(cls, *args, **kwargs):
        cls._instances = ExpiringDict(max_len=1000, max_age_seconds=1800)
        
    def __call__(cls, callid, *args, **kwargs):
        try:
            instance = cls._instances[callid]
            return instance
        except KeyError:
            instance = super().__call__(callid, *args, **kwargs)
            cls._instances[callid] = instance
            return instance
            
    def remove(cls, callid):
        logging.debug(f"Remove {callid}")
        del(cls._instances[callid])
    
class CallManager(metaclass=CallidSingleton):
    def __init__(self, callid, phone, extend_list, retry_count=3):
        self.callid = callid
        self.phone = phone
        self.extend = "#".join(map(lambda x : str(x), extend_list))
        self.retry_count = retry_count
        self.last_list_id = None
        
    def _have_call(self):
        return self.last_list_id != None
        
    def _call(self):
        self.last_list_id = insert_buslist(self.phone,self.extend)
        self.retry_count = self.retry_count - 1
    
    def _should_retry(self):
        return self.retry_count > 0
        
    def _destroy(self):
        self.__class__.remove(self.callid)
        
    def response(self, resp, *args):
        res = resp.render(*args)
        if resp.is_terminal():
            self._destroy()
        return (res, resp.is_terminal())
        
    def recall_with_response(self):
        if self._should_retry():
            self._call()
            return self.response(Response.RETRY, self.retry_count)
        else:
            return self.response(Response.FAIL)
            
    def process(self):
        # 如果没有呼叫过
        if not self._have_call():
            logging.info(f"如果没有呼叫过,{self.last_list_id}")
            self._call()
            return self.response(Response.CONNECTING, 3 - self.retry_count)
        cti_status = cti_cdr(self.last_list_id)
        # 数据库中没有查到,在呼叫中.
        if cti_status == None:
            logging.info("数据库中没有查到,在呼叫中")
            return self.response(Response.CONNECTING, 3 - self.retry_count)
        # 用户接通且用户主动挂机返回值200
        if cti_status == 200:
            bot_res = bot_result(self.callid)
            if bot_res == 0:
                logging.info("用户挂机了但没给返回")
                return self.recall_with_response()
            elif bot_res == 200:
                logging.info("用户同意挪车")
                return self.response(Response.ACCEPT_200)
            elif bot_res == 300:
                logging.info("用户拒绝挪车")
                return self.response(Response.REJECT_300)
            elif bot_res == 401:
                logging.info("错误的车主")
                return self.response(Response.WRONG_USER_401)
            elif bot_res == 402:
                logging.info("错误的停车地点")
                return self.response(Response.WRONG_LOCATION_402)
            else:
                logging.info("未知的错误")
                return self.response(Response.UNKNOW)
        # 用户拒绝接听603,或者其他大于400造成的失败    
        if cti_status == 603 or cti_status > 400:
            logging.info("用户拒绝接听603,或者其他大于400造成的失败")
            return self.recall_with_response()
        # 用户接通返回是0,有可能后续接通后改成返回200
        if cti_status == 0:
            logging.info("用户接通返回是0,有可能后续接通后改成返回200")
            return self.response(Response.CONNECTED)
        
        return self.response(Response.UNKNOW)
    
def automap():
    from sqlalchemy.ext.automap import automap_base
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine

    Base = automap_base()
    # reflect the tables
    Base.prepare(engine, reflect=True)

    Base = automap_base()
    Base.prepare(engine, reflect=True)

    OcmBuslist = Base.classes.ocm_buslist
    print(OcmBuslist)
    import pdb
    pdb.set_trace()
    session = Session(engine)

    res = session.query(OcmBuslist).first()
    print(res)
    
def test_meta_class():
    p = CallManager("1",999991,["11000000", "津A12345", "滨海新区", "挡住出车道"])
    print(p.retry_count)
    p.retry_count = p.retry_count - 1
    p.last_list_id = 10
    # p._destroy()
    p1 = CallManager("1",999991,["11000000", "津A12345", "滨海新区", "挡住出车道"])
    print(p1.retry_count)
    print(p1.last_list_id)
    
if __name__ == "__main__":
    import time
    # res = insert_buslist(999991,'11000000#津A12345#滨海新区#挡住出车道')
    # print(res)

    #automap()
    #print(cti_cdr(204531))
    DEBUG=True
    #create_call_result()
    while True:
        p = CallManager("1",999991,["11000000", "津A12345", "双清大厦", "挡住出车道"])
        logging.info(p.process()[0])
        time.sleep(1)
        # if input('continue? (Y?n)').lower() == 'n':
        #     break

# from sqlalchemy import create_engine, MetaData, Table, Column, ForeignKey
# from sqlalchemy.ext.automap import automap_base
# # produce our own MetaData object
# metadata = MetaData()
#
# # we can reflect it ourselves from a database, using options
# # such as 'only' to limit what tables we look at...
# metadata.reflect(engine, only=['ocm_buslist'])
#
# Base = automap_base(metadata=metadata)
#
# OcmBuslist = Base.classes.ocm_buslist
#
#
# print(metadata)
#
# print(Base)
# print(OcmBuslist)
# mapped classes are now created with names by default
# matching that of the table name.

#
# session = Session(engine)
#
# # rudimentary relationships are produced
# OcmBuslist = Base.classes.ocm_buslist
#
# u1 = session.query(OcmBuslist).first()
# print (u1)