from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
Session = sessionmaker(bind=engine)
res = engine.execute("Select count(*) from ocm_buslist")

def init_cti_cdr_trigger():
    engine.execute("""
    CREATE TRIGGER cti_cdr_trigger AFTER INSERT OR UPDATE ON cti_cdr
      FOR EACH ROW
      BEGIN
        INSERT INTO test2 SET a2 = NEW.dropcause;
        DELETE FROM test3 WHERE a3 = NEW.a1;
        UPDATE test4 SET b4 = b4 + 1 WHERE a4 = NEW.a1;
      END;
    """)
    pass
    
def init_ocm_bot_result_trigger():
    pass
    
def init_event_table(list_id):
    pass
    
def clear_init():
    pass

def insert_cti_cdr(dropcause):
    engine.execute("""
    INSERT INTO table_name () VALUES ()
    """)
    pass
    
def insert_buslist():
    pass
    
def insert_event():
    pass
    
def event():
    pass

print(res.next())

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

Base = automap_base()
Base.prepare(engine, reflect=True)

OcmBuslist = Base.classes.ocm_buslist
session = Session(engine)

res = session.query(OcmBuslist).first()
print(res)

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