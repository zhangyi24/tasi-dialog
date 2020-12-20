import logging
from types import SimpleNamespace
from .callwatcher.client import CallManager
ENV="dev"

if ENV == "production":
    from .api.soap_api import query
else:
    from .api.json_api import query

## order_time
def query_phone_by_car_no(user_utter, global_vars, context = None):
    ENDPOINT="users"
    logging.info(f"query_phone_by_car_no: user_utter={user_utter}, context={context}")
    data = query(ENDPOINT, car_no=global_vars['car_no'])
    if not data:
        return False
    else:
        global_vars['phone_no'] = data['phone']
        return True
        
def call_manager_process(user_utter, global_vars, context = None):
    ns = SimpleNamespace(**context)
    call_id = ns.call_info['call_id']
    extend = ns.call_info['user_info']
    # global variables
    phone = global_vars['phone_no']
    car_no = global_vars['car_no']
    car_location = global_vars['car_location']
    car_move_reason = global_vars['car_move_reason']
    logging.info(f"call_manager_process: call_id={call_id}, phone={phone}, car_no={car_no}, car_location={car_location}, car_move_reason={car_move_reason}")
    manager = CallManager(call_id, phone, [call_id, car_no, car_location, car_move_reason])
    msg,code = manager.process()
    # Tricky地用global_vars来返回结果
    global_vars['func_message'] = msg
    return code

if __name__ == "__main__":
    car_no = "津A12345"
    res = query(f'users',car_no=car_no)
    global_vars = {'car_no': car_no}
    p_res = query_phone_by_car_no({},global_vars)
    print("query result:", res)
    print(p_res, global_vars)