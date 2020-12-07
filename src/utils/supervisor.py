import os
TEMPLATE = os.path.realpath(os.path.dirname(__file__) + "/program.ini")
## supervisor
SUPERVISOR_CONFIG = "/usr/local/etc/supervisord.ini"
SUPERVISOR_PROGRAM_CONFIG = "/usr/local/etc/supervisor.d/"
PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__) + "../../../")
PATH = "/Users/luxin433/.pyenv/shims/"

def write_program(project_name, project_root, cmd, program_name, path):
    template = open(TEMPLATE,'r').read()
    params = {}
    for i in ('project_name', 'project_root', 'cmd', 'program_name', 'path'):
        params[i] = locals()[i]
    res = template.format(**params)
    program_config = SUPERVISOR_PROGRAM_CONFIG + f"{program_name}.ini"
    print("write config:", program_config)
    with open(program_config,'w') as f:
        f.write(res)
        
def write_crs():
    write_program("dialog", PROJECT_ROOT, "python src/server_crs.py", "crs", PATH)
        
def write_bot(bot_path, bot_type="text"):
    if bot_type != "text":
        bot_type = "phone"
    write_program("dialog", os.path.join(PROJECT_ROOT, f"bots/{bot_path}"), f"bash run_server_{bot_type}.sh", f"{bot_path}_{bot_type}", PATH)
    
def exec(string):
    print(string)
    os.system(string)
    
    
def main(argv):
    import argparse
    # Create a parser
    parser = argparse.ArgumentParser(description='Config Writer')
    # Add argument
    parser.add_argument('env', default="local", help="environment")
    args = parser.parse_args(argv)
    if args.env == 'docker':
        import os
        conf = os.path.realpath(os.path.dirname(__file__) + "/supervisord.ini")
        exec(f"mkdir -p {SUPERVISOR_PROGRAM_CONFIG}")
        exec(f"cp {conf} {SUPERVISOR_CONFIG}")
        exec(f"mkdir -p /usr/local/var/log/dialog")
        exec(f"mkdir -p /usr/local/var/run")
    
    write_crs()
    write_bot("hnyc", "phone")
    write_bot("hnyc", "text")
    write_bot("hnyc_survey", "phone")
    write_bot("hnyc_survey", "text")
    
def start():
    exec(f"supervisord -c {SUPERVISOR_CONFIG}")
    
def install():
    pass 
if __name__ == "__main__": 
    import sys
    main(sys.argv[1:])
