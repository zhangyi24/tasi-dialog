import json
import os
import glob


def extract_responses_from_config(config_dir):
    responses = set()
    responses.update(extract_responses_from_flows(config_dir))
    responses.update(extract_responses_from_service_language(config_dir))
    return list(responses)


def extract_responses_from_flows(config_dir):
    responses = set()
    flows_path = os.path.join(config_dir, 'flows', '*.json')
    for flow_path in glob.glob(flows_path):
        responses.update(extract_responses_from_flow(flow_path))
    return responses


def extract_responses_from_flow(flow_path):
    responses = set()
    with open(flow_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    nodes = config['nodes']
    for node in nodes.values():
        if node['type'] == 'slot_filling':
            for slot in node['slots']:
                resp = slot.get('response', '')
                if resp != '':
                    responses.add(resp)
        elif node['type'] == 'response':
            responses.add(node['response'])

        dm = node.get('dm', [])
        for branch in dm:
            resp = branch.get('response', '')
            if resp != '':
                responses.add(resp)
    return responses


def extract_responses_from_service_language(config_dir):
    responses = set()
    service_language_path = os.path.join(config_dir, 'service_language.json')
    if not os.path.exists(service_language_path):
        return set()
    with open(service_language_path, 'r', encoding='utf-8') as f:
        service_languages_path = json.load(f)
    responses.update(set(service_languages_path.values()))
    return responses


if __name__ == '__main__':
    config_dir = '.'
    resps = extract_responses_from_config(config_dir)
    with open('bot_responses.json', 'w', encoding='utf-8') as f:
        json.dump(resps, f, ensure_ascii=False, indent=2)
