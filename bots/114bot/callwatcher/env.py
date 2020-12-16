from environs import Env
from ..
env = Env()
env.read_env()

def mysql_url():
    return "{dialect}+{driver}://{username}:{password}@{host}:{port}/{database}"
    
def read(prefix, key):
    with env.prefixed(prefix):
        value = env(key, None)
        if not value: 
            raise Exception('spam', 'eggs')        
        port = env.int("PORT", 5000)  # => 3000
        
    if not env(key):
        throw 
    