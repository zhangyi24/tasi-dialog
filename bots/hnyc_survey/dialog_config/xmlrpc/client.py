import xmlrpc.client

s = xmlrpc.client.ServerProxy('http://localhost:8000')


def test_answer():
    sentences1 = ['很满意','基本满意','不满意']
    answer1 = ['狠满意','太烂了','牛逼上天了','烂透了','马马虎虎']
    for ans in answer1:
        print(s.distance(sentences1, ans))
            
test_answer()