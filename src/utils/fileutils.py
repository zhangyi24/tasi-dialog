import os, json, sys
from .richlogger import Logger
from pathlib import Path
logger = Logger(__file__)

def json_load(*args, default=None):
    path = filepath(*args)
    if not Path(path).exists():
        logger.warning(f"File {path} not exist")
        return default
        
    with open(path, 'r', encoding='utf-8') as f:
        try: 
            res = json.load(f)
            return res
        except Exception as e:
            logger.error(f"Parse JSON file {path}")
            logger.exception(e)
            return default
    
def joinpath(*args):
    path = Path(args[0])
    for e in args[1:]:
        path = path.joinpath(e)
    return path.resolve()
    
def dirpath(*args):
    path = joinpath(*args)
    if not path.exists():
        raise Exception(f"Path {path} not exist")
    if not path.is_dir():
        raise Exception(f"Not Dir {path}")
    return path.resolve()
    
def filepath(*args, ensure=False):
    path = joinpath(*args)
    if not path.exists():
        if not ensure:
            raise Exception(f"Path {path} not exist")
        else:
            path.touch()
    if not path.is_file():
        raise Exception(f"Not File {path}")
    return path.resolve()
    
def test_dirpath():
    res = dirpath(__file__, "../../tt")
    print(type(res))
    
def test_dirpath1():
    print(dirpath(__file__))
    
def test_json_load():
    json_load('bots/114bot_out/dialog_config/global_vars.json')
    json_load('bots/114bot_out/dialog_config/functions.py', default={})
    
if __name__ == "__main__":
    pass