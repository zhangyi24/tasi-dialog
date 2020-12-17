import logging
ENV="dev"

if ENV == "production":
    from .api.soap_api import query
else:
    from .api.json_api import query

## order_time
def query_phone_by_car_no(user_utter, global_vars):
    ENDPOINT="users"
    logging.debug(f"query_phone_by_car_no: user_utter={user_utter}, global_vars={global_vars}")
    data = query(ENDPOINT, car_no=global_vars['car_no'])
    if not data:
        return False
    else:
        global_vars['phone_no'] = data['phone']
        return True

if __name__ == "__main__":
    car_no = "津A12345"
    res = query(f'users',car_no=car_no)
    global_vars = {'car_no': car_no}
    p_res = query_phone_by_car_no({},global_vars)
    print("query result:", res)
    print(p_res, global_vars)