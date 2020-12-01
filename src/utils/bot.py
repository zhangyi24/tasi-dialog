'''
bot总控脚本(未完成)
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
from config_writer import print_routes
import supervisor

BOT_FOLDER = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../bots"))
def _bot_choices():
    bot_choices = glob.glob(BOT_FOLDER+"/*",recursive=False)
    bot_choices = [os.path.basename(path) for path in bot_choices]
    return bot_choices

from pathtype import PathType

def bot_new(args):
    pass
    
def bot_derive(args):
    pass
    
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