import yaml, os
BOT_PATH = os.path.realpath(os.path.dirname(__file__) + "/../../bots")
CONFIG_FILE = os.path.realpath(os.path.dirname(__file__) + "/../config/config.yml")
if not os.path.exists(CONFIG_FILE):
    raise Exception('I/O error', f"{CONFIG_FILE} not exist.")
config = yaml.load(open(CONFIG_FILE,'r'), Loader=yaml.FullLoader)

from port import free_port

def add_route(bot_id):
    port = free_port()
    routes()[bot_id] = f"http://127.0.0.1:{port}"
    yaml.dump(config, open(CONFIG_FILE,'w'))
    return bot_id, port
    
def modify_bot_port(bot_id, port):
    bot_name, bot_type = bot_id.split("-")
    bot_config_path = os.path.join(BOT_PATH, bot_name, "config.yml")
    print(f"Modify bot config {bot_config_path} with {bot_type} port to {port}")
    bot_config = yaml.load(open(bot_config_path,'r'), Loader=yaml.FullLoader)
    bot_config[bot_type]['port'] = port
    yaml.dump(bot_config, open(bot_config_path,'w'))    
    
def routes():
    return config['crs']['route']
    
def print_routes():
    d = routes()
    print("{:<15} {:<15}".format('BotEntranceId','Service'))
    for k, v in d.items():
        print("{:<15} {:<15}".format(k, v))

if __name__ == "__main__":
    import argparse
    # Create a parser
    parser = argparse.ArgumentParser(description='Config Writer')
    # Add argument
    parser.add_argument('--bot_id', default="10", help="bot id")
    args = parser.parse_args()
    bot_id, port = add_route(args.bot_id)
    print(bot_id, port)