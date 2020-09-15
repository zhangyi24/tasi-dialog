import collections

def merge_config(conf1, conf2):
    """merge conf2 into conf1"""
    queue = collections.deque([(conf1, conf2)])
    while queue:
        dict1, dict2 = queue.popleft()
        for key in dict1:
            if key in dict2:
                if type(dict1[key]) == dict and type(dict2[key]) == dict:
                    queue.append((dict1[key], dict2[key]))
                else:
                    dict1[key] = dict2[key]

if __name__ == "__main__":
    conf_1 = {"a": 1, "b": 2, "c": {"d": 3, "e": {"f": 4, "g": [5]}}}
    conf_2 = {"c": {"e": {"f": [4, 7], "g": 0}}}
    merge_config(conf_1, conf_2)
    print(conf_1, conf_2)