'''
bot总控脚本
## bot 生成
bot new `$folder_path` #从路径下的配置文件中生成一个新的bot.
bot derive bot_name `data.json` #以某个bot为模板派生出一个bot来,用于调查问卷的bot生成,返回bot_id

## bot 配置
bot config # 配置bot的各种参数
bot init
bot status

## bot 进程管理
bot install `$bot_id`
bot run `$bot_id`
bot stop `$bot_id`
bot restart `bot_id`

## bot 状态管理
bot cli `$bot_id` # 启动某个bot的文字版会话
bot cli crs # 从crs启动会话测试
'''

import glob, os, sys
from config_writer import print_routes, add_route, modify_bot_port
import supervisor
from supervisor import write_bot

BOT_FOLDER = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../bots"))
def _bot_choices():
    bot_choices = glob.glob(BOT_FOLDER+"/*",recursive=False)
    bot_choices = [os.path.basename(path) for path in bot_choices]
    return bot_choices

from pathtype import PathType

def bot_new(args):
    pass
    
def bot_derive(args):
    bot_path = os.path.join(BOT_FOLDER, args.botname)
    if not os.path.exists(bot_path):
        print(f"Error, bot path {bot_path} not exists.")
    else:
        print(f"Derive bot from {bot_path}")
    i = 1
    while os.path.exists(os.path.join(BOT_FOLDER, f"{args.botname}_{i}")):
        i = i + 1
        
    new_bot_name = f"{args.botname}_{i}"
    new_bot_path = os.path.join(BOT_FOLDER, new_bot_name)
    print(f"Generate new bot at {new_bot_path}")
    os.system(f"cp -r {bot_path} {new_bot_path}")
    ori_quest = os.path.join(args.source, "data.json")
    dst_quest = os.path.join(new_bot_path, "data", "question-raw.json")
    print(f"Import data from {ori_quest} to {dst_quest}")
    os.system(f"cp {ori_quest} {dst_quest}")
    # Generate phone bot
    phone_bot, phone_bot_port = add_route(f"{new_bot_name}-phone")
    print(f"Register Phone Bot route {phone_bot} at port {phone_bot_port}")
    modify_bot_port(phone_bot, phone_bot_port)
    write_bot(new_bot_name, "phone")
    # Generate text bot 
    text_bot, text_bot_port = add_route(f"{new_bot_name}-text")
    print(f"Register Text Bot route {text_bot} at port {text_bot_port}")
    modify_bot_port(text_bot, text_bot_port)
    write_bot(new_bot_name, "text")
    
def bot_init(args):
    print("\n[install supervisor]")
    supervisor.main(['docker'])
    print("\n[start supervisor daemon]")
    supervisor.start()
    bot_status(args)

def bot_status(args):
    print("\n[supervisorctl]")
    os.system('supervisorctl status')
    print("\n[Bot Routes]")
    print_routes()
    
def bot_install(args):
    pass
    
def bot_run(args):
    pass
    
def bot_stop(args):
    pass
    
def bot_restart(args):
    pass
    
def bot_cli(args):
    pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog='bot')
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')
    # create the parser for the "new" command
    parser_new = subparsers.add_parser('new', help='bot new')
    parser_new.add_argument('source', type=PathType(exists=True, type='dir'), help='bot config data source')
    # create the parser for the "derive" command
    parser_new = subparsers.add_parser('derive', help='bot derive')
    parser_new.add_argument('botname', choices=_bot_choices(), help='bot name')
    parser_new.add_argument('source', type=PathType(exists=True, type='dir'), help='bot config data source')
    # create the parser for the "install" command
    parser_new = subparsers.add_parser('init', help='bot system init')
    # create the parser for the "status" command
    parser_new = subparsers.add_parser('status', help='bot status')
    # create the parser for the "run" command
    parser_new = subparsers.add_parser('run', help='bot run')
    parser_new.add_argument('botid', type=str, help='bot id')
    # create the parser for the "run" command
    parser_new = subparsers.add_parser('stop', help='bot run')
    parser_new.add_argument('botid', type=str, help='bot id')
    # create the parser for the "run" command
    parser_new = subparsers.add_parser('restart', help='bot run')
    parser_new.add_argument('botid', type=str, help='bot id')
    # create the parser for the "cli" command
    parser_new = subparsers.add_parser('cli', help='bot cli')
    parser_new.add_argument('botid', type=str, help='bot id')
    # parse some argument lists
    
    args = parser.parse_args()    
    if not args.command:
        parser.print_help()
    else:
        #os.system('supervisorctl status')
        res = globals()[f'bot_{args.command}'](args)
            
            
    # args = parser.parse_args(['new', './'])
    # print(parser.parse_args(['derive', 'hnyc_survey', '.']))
    # globals()[f'bot_{args.command}'](args)