import xmlrpc.client

def rpcserver(domain, port):
    return xmlrpc.client.ServerProxy(f"http://{domain}:{port}")

def test_answer():
    s = server("localhost",8000)
    sentences1 = ['很满意','基本满意','不满意']
    answer1 = ['狠满意','太烂了','牛逼上天了','烂透了','马马虎虎']
    for ans in answer1:
        print(s.distance(sentences1, ans))
            
if __name__ == "__main__":
    test_answer()