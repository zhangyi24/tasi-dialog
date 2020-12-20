import logging
from types import SimpleNamespace
from .callwatcher.client import insert_callout_result

## functions
def write_result(user_utter, global_vars, context = None):
    logging.info(f"write_result: user_utter={user_utter}, context={context}")
    ns = SimpleNamespace(**context)
    call_id = ns.call_info['call_id']
    extend = ns.call_info['user_info']
    stringToInt = extend.split("#")[0]
    try:
      from_callid = int(stringToInt)
    except ValueError:
      from_callid = 123
    content = None
    # global variables
    call_result = global_vars['agree_move_car']
    logging.info(f"write_result: extend={extend},call_result={call_result}")
    insert_callout_result(call_id, from_callid, content, extend, call_result)
    return True

if __name__ == "__main__":
    car_no = "津A12345"
    res = query(f'users',car_no=car_no)
    global_vars = {'car_no': car_no}
    p_res = query_phone_by_car_no({},global_vars)
    print("query result:", res)
    print(p_res, global_vars)
    
