import logging
ENV="dev"

if ENV == "production":
    from .api.soap_api import query
else:
    from .api.json_api import query

## order_time
def order_time_access_by_phone_no(user_utter, global_vars):
    ENDPOINT="custInfoQuery"
    logging.debug(f"order_time_access_by_phone_no: user_utter={user_utter}, global_vars={global_vars}")
    data = query(ENDPOINT, phone_no=global_vars['phone_no'])
    if not data:
        return False
    else:
        global_vars['order_time'] = data
        return True
    
def order_time_access_by_cert_no(user_utter, global_vars):
    ENDPOINT="custInfoQuery"
    logging.debug(f"order_time_access_by_cert_no: user_utter={user_utter}, global_vars={global_vars}")
    data = query(ENDPOINT, cert_no=global_vars['cert_no'])
    if not data:
        return False
    else:
        global_vars['order_time'] = data
        return True
        
def report_order_time(user_utter, global_vars): 
    if ENV == "production":
        return global_vars['order_time']
    else: 
        sales = global_vars['order_time']['sales']
        sales_phone = global_vars['order_time']['sales_phone']
        return f"您的售货员是{sales},售货员电话{sales_phone}"
             
## order_info
def order_info_access_by_phone_no(user_utter, global_vars):
    ENDPOINT="orderInfoQuery"
    logging.debug(f"order_info_access_by_phone_no: user_utter={user_utter}, global_vars={global_vars}")
    data = query(ENDPOINT, phone_no=global_vars['phone_no'])
    if not data:
        return False
    else:
        global_vars['order_info'] = data
        return True
    
def order_info_access_by_cert_no(user_utter, global_vars):   
    ENDPOINT="orderInfoQuery"
    logging.debug(f"order_info_access_by_cert_no: user_utter={user_utter}, global_vars={global_vars}")
    data = query(ENDPOINT, cert_no=global_vars['cert_no'])
    if not data:
        return False
    else:
        global_vars['order_info'] = data
        return True
        
def report_order_info(user_utter, global_vars): 
    if ENV == "production":
        return global_vars['order_info']
    else: 
        sales = global_vars['order_info']['sales']
        sales_phone = global_vars['order_info']['sales_phone']
        return f"您的售货员是{sales},售货员电话{sales_phone}"
        
## customer_info
def customer_info_access_by_phone_no(user_utter, global_vars):
    ENDPOINT='custInformation'
    logging.debug(f"customer_info_access_by_phone_no: user_utter={user_utter}, global_vars={global_vars}")
    data = query(ENDPOINT, phone_no=global_vars['phone_no'])
    if not data:
        return False
    else:
        global_vars['customer_info'] = data
        return True

def customer_info_access_by_cert_no(user_utter, global_vars):   
    ENDPOINT='custInformation'
    logging.debug(f"customer_info_access_by_cert_no: user_utter={user_utter}, global_vars={global_vars}")
    data = query(ENDPOINT, cert_no=global_vars['cert_no'])
    if not data:
        return False
    else:
        global_vars['customer_info'] = data
        return True
    
def report_customer_info(user_utter, global_vars): 
    if ENV == "production":
        return global_vars['customer_info']
    else: 
        sales = global_vars['customer_info']['sales']
        sales_phone = global_vars['customer_info']['sales_phone']
        return f"您的售货员是{sales},售货员电话{sales_phone}"
        
## customer_manager_info
def customer_manager_info_access_by_phone_no(user_utter, global_vars):
    ENDPOINT="custMgrQuery"
    logging.debug(f"customer_manager_info_access_by_phone_no: user_utter={user_utter}, global_vars={global_vars}")
    data = query(ENDPOINT, phone_no=global_vars['phone_no'])
    if not data:
        return False
    else:
        global_vars['customer_manager_info'] = data
        return True
    
def customer_manager_info_access_by_cert_no(user_utter, global_vars):   
    ENDPOINT="custMgrQuery"
    logging.debug(f"customer_manager_info_access_by_cert_no: user_utter={user_utter}, global_vars={global_vars}")
    data = query(ENDPOINT, cert_no=global_vars['cert_no'])
    if not data:
        return False
    else:
        global_vars['customer_manager_info'] = data
        return True
        
def report_customer_manager_info(user_utter, global_vars): 
    if ENV == "production":
        return global_vars['customer_manager_info']
    else: 
        sales = global_vars['customer_manager_info']['sales']
        sales_phone = global_vars['customer_manager_info']['sales_phone']
        return f"您的售货员是{sales},售货员电话{sales_phone}"
        
## addr_search
def addr_search_access_by_address(user_utter, global_vars):
    ENDPOINT="addrSearch"
    logging.debug(f"addr_search_access_by_address: user_utter={user_utter}, global_vars={global_vars}")
    data = query(ENDPOINT, phone_no=global_vars['address'])
    if not data:
        return False
    else:
        global_vars['addr_search'] = data
        return True
    
def report_addr_search(user_utter, global_vars): 
    if ENV == "production":
        return global_vars['addr_search']
    else: 
        sales = global_vars['addr_search']['sales']
        sales_phone = global_vars['addr_search']['sales_phone']
        return f"您的售货员是{sales},售货员电话{sales_phone}"


if __name__ == "__main__":
    phone_no = 13588880000
    cert_no = 22345678
    res = query(f'users',cert_no=cert_no)
    order_time_access_by_phone_no({},{'phone_no': phone_no})
    print(res)
     
    
