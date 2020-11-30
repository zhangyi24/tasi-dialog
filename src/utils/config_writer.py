import yaml, os
CONFIG_FILE = os.path.realpath(os.path.dirname(__file__) + "/../config/config.yml")
if not os.path.exists(CONFIG_FILE):
    raise Exception('I/O error', f"{CONFIG_FILE} not exist.")
config = yaml.load(open(CONFIG_FILE,'r'), Loader=yaml.FullLoader)

from free_port import free_port

def add_route(bot_id):
    port = free_port()
    routes()[bot_id] = f"http://127.0.0.1:{port}"
    yaml.dump(config, open(CONFIG_FILE,'w'))
    return bot_id, port
    
def routes():
    return config['crs']['route']

if __name__ == "__main__":
    import argparse
    from types import SimpleNamespace
    # Create a parser
    parser = argparse.ArgumentParser(description='Config Writer')
    # Add argument
    parser.add_argument('--bot_id', default="10", help="bot id")
    args = vars(parser.parse_args())
    args = SimpleNamespace(**args)
    bot_id, port = add_route(args.bot_id)
    print(bot_id, port)