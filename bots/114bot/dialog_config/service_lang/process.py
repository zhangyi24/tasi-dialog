import pandas as pd
import os, math
import csv
EXCEL_FILE = os.path.realpath(os.path.dirname(__file__) + "/挪车话术脚本整理.xls")
OUTPUT_FILE = os.path.realpath(os.path.dirname(__file__) + "/output.csv")
df = pd.read_excel(EXCEL_FILE, index_col=0)
key = df['服务环节'].dropna()
#print(key.to_string(index=False))

KEY_MAPPING = {
"确认挪车服务":"confirm_move",
"无挪车需求":"deny_move",
"转接人工":"forward",
"询问车牌":"ask_car_no",
"确认车牌":"confirm_car_no",
"车牌不符":"wrong_car_no",
"询问地址":"ask_location",
"确认挪车地址":"confirm_location",
"询问挪车原因":"ask_reason",
"确认挪车原因":"confirm_reason",
"向客户说明开始挪车":"move_car_succ",
"向客户说明无法挪车":"move_car_fail",
"确认车主":"confirm_owner",
"确认地址":"confirm_car_location",
"说明挪车原因":"tell_move_car_reason",
"与车主交互":"feedback_owner",
"反馈车主回馈（配合）":"feedback_owner_accept",
"反馈车主回馈（不配合）":"feedback_owner_reject",
"其他交互":"other"
}

KEY=""
INDEX=0
def get_key(key):
    global KEY, INDEX
    #print(key, type(str(key)), str(key) == "nan")
    if str(key) != "nan":
       KEY = KEY_MAPPING[key]
       INDEX = 0
       return KEY
    else:
       INDEX += 1
       return f"{KEY}{INDEX}"
       
def render(key, value):
    return f"\"{key}\":\"{value}\","

df['KEY'] = df['服务环节'].apply(get_key)
df['res'] = df.apply(lambda x: render(x['KEY'], x['提示音脚本']), axis=1)
df['res'].to_csv(OUTPUT_FILE, index=False, header=False, quoting=csv.QUOTE_NONE, escapechar='\\')
#with open(OUTPUT_FILE,'w') as f:
#    f.write(df['res'].to_string(index=False))

    

    
