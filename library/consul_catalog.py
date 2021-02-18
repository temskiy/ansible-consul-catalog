#!/usr/bin/python3

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview']
}

DOCUMENTATION = '''
---
module: consul_catalog

short_description: Module to register and deregister nodes to the Consul catalog.

version_added: "2.7"

author:
    - @lobstermania

description:
 - Allows the addition and deletion of nodes from the Consul catalog. See https://www.consul.io/api/catalog.html.

options:
  consul_host:
    description:
      - The Consul endpoint to connect to.
    required: false
    default: localhost
  consul_port:
    description:
      - The Consul port to connect to.
    required: false
    default: 8500
  token:
    description:
      - ACL token.
    required: false
  node: 
    description:
      - The catalog node to add or remove
    required: true
  dc:
    description:
      - The Consul DC to work with
    default: dc1
  address:
    description:
      - The catalog node's address
    required: false
  scheme:
    description:
      - The scheme to connect to Consul
    default: http
    required: false
    choices: ['http','https']
  verify:
    description:
      - Verify Consul endpoint (used in conjunction with https scheme)
    default: false
    required: false
  state:
    description:
      - Add or remove the node
    default: present
    required: false
    choices: ['present','absent']
  service_name:
    description:
      - Service name
    required: false
  service_id:
    description:
      - Service ID
    required: false
  service_port:
    description:
      - Service port
    defaut: 0
    required: false
  service_tags:
    description:
      - Service tags
    required: false

requirements:
  - "python >= 2.7"
  - python-consul

'''

EXAMPLES = '''
    - consul_catalog:
        node: "db1.example.net"
        address: "db1.example.net"
        state: present
        token: "notcheese"
        service_name: "postgres"
        service_id: "db1_postgres"
        service_port: 5432
        service_tags:
          - master
          - v1

'''

from ansible.module_utils.basic import *
import consul,json,ast

def main():
    
    fields = {
        "consul_host": {"required": False, "type":"str", "default":"localhost"},
        "consul_port": {"required": False, "type":"int", "default":8500},
        "token": {"required": False, "type":"str", "default":""},
        "node": {"required": True, "type":"str"},
        "dc": {"required": False, "type":"str", "default":""},
        "address": {"required": False, "type":"str"},
        "scheme": {"required": False, "type":"str", "choices":['http','https'],"default":"http"},
        "verify": {"required": False, "type":"bool", "default":False},
        "state": {"required": False, "type":"str", "choices":['present','absent'],"default":"present"},
        "service_name": {"required": False, "type":"str", "default":""},
        "service_id": {"required": False, "type":"str", "default":""},
        "service_port": {"required": False, "type":"int", "default":0},
        "service_tags": {"required": False, "type":"list", "default":""}
    }

    module = AnsibleModule(argument_spec=fields,supports_check_mode=False)
    c,cc = load_consul(module.params,module)

    if module.params["state"] == "present":
        has_changed,result = register_node(module.params,cc)
    elif module.params["state"] == "absent":
        has_changed,result = deregister_node(module.params,cc)
    
    module.exit_json(changed=has_changed,meta=result)

def load_consul(params,module):
    try:
        c = consul.Consul(host=params['consul_host'],verify=params['verify'],token=params['token'],dc=params['dc'],port=params['consul_port'],scheme=params['scheme'])
    except Exception as e:
        sys.exit(1)
    cc = c.catalog
    return c,cc

def check_node_exists(params,cc):
    nodes = cc.nodes()[1]
    exists = False
    for node in nodes:
        if node['Node'] == params['node']:
            exists = True
    return exists
    
def register_node(params,cc):
    r = cc.register(params['node'],params['address'],dc=params['dc'],service={ "Service": params['service_name'], "ID": params['service_id'], "Tags": params['service_tags'], "Port": params['service_port'] })
    has_changed = True
    result = r
    return has_changed,result

def deregister_node(params,cc):
    node_exists = check_node_exists(params,cc)
    if node_exists:
        r = cc.deregister(params['node'],service_id=params['service_id'])
        has_changed = True
        result = r
    else:
        has_changed = False
        result = ""
    return has_changed,result

if __name__ == '__main__':
	main()
