from elasticsearch import Elasticsearch
import json
# todo: 读取config
index = '95598'
doc_type = 'question'
address = '127.0.0.1:9200'
es = Elasticsearch(address)
try:
	res = es.indices.delete(index=index)
except:
	print(index, '不存在')
#创建索引
mappings = {
	"properties": {
		"label": {
			"type": "text",
			"analyzer": "ik_max_word",
			"index_options": "docs"
		},
		"id": {
			"type": "text"
		}
	}
}
# print(mappings)

result = es.indices.create(index=index, body=mappings, ignore = 400)
# print(result)

#添加索引
with open('question.txt', 'r', encoding='utf-8') as fr:
	lines = fr.readlines()
	for line in lines:
		line = json.loads(line)
		label = line['label']
		_id = line['id']
		action = {"label": label,"id": _id}
		res = es.index(index=index,doc_type=doc_type,body = action, id=_id )
		# re = es.update(index=index,doc_type=doc_type,body=action,id=_id) # 更新索引
		# print(res)
# # success, _ = bulk(es, ACTIONS, index=index, raise_on_error=True)