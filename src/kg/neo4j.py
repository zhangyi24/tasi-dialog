from py2neo import Graph, Node, Relationship, cypher, Path

class Neo4j():
	graph = None
	def __init__(self, address, username, password):
		self.address = address
		self.username = username
		self.password = password
		self.graph = Graph(self.address, username=self.username, password=self.password)

	def matchQuestionbyId(self, node_id, location=""):
		
		node_id = str(node_id)
		if len(location) > 0:
			sql = 'MATCH (n:Question)-[r]-(n2:Answer)-[r2]-(n3:Range) WHERE ID(n)=' + node_id + ' and n3.title="' + location + '" return n2.content as content';
		else:
			sql = 'MATCH (n:Question)-[r]-(n2:Answer)-[r2]-(n3:Range) WHERE ID(n)=' + node_id + ' return n2.content as content limit 1';
		
		answer = self.graph.run(sql).data()
		# print(len(answer))
		data = {}
		if len(answer[0]) == 0:
			return data
		tmp = answer[0]
		content = tmp.get('content')
		
		data.update({'content':content})
		arrs = []
		sql = 'MATCH (n:Question)-[r]-(n2:Instance)-[r2]-(n3:Question) WHERE ID(n)=' + node_id + ' return n3.title as title, ID(n3) as id';
		related = self.graph.run(sql).data()
		for tmp in related:
			title = tmp.get('title')
			_id = tmp.get('id')
			node = {"label":title, "id":_id}
			arrs.append(node)
		data.update({'related':arrs})
		return data