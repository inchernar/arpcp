#!/usr/bin/env python3

import arpcp

node1 = arpcp.RemoteNode('192.168.1.5')
# node1 = arpcp.RemoteNode('192.168.1.116')
# print(node1.procedures)
# print(node1.procedures.multiple(2, 1))
# print(node1.procedures.async_multiple(2,11))
# print(node1.procedures.multiple(2.02, 5.823))
# print(node1.procedures.async_func1())


# print(arpcp.ARPCP.call('192.168.1.115', 7018, 'procedures1', {}))
# print(arpcp.ARPCP.call('192.168.1.5', 7018, 'procedures', {}))
# print(arpcp.ARPCP.call('192.168.1.115', 7018, 'procedures', {'ads': 'qwe'}))
# print(arpcp.ARPCP.call('192.168.1.115', 7018, 'task', {'remote_procedure': 'func1'}))
# print(arpcp.ARPCP.call('192.168.1.5', 7018, 'atask', {
# 	'remote_procedure': 'multiple',
# 	'remote_procedure_args': [2, 4]
# }))
# print(arpcp.ARPCP.call('192.168.1.5', 7018, 'task', {
# 	'remote_procedure': 'func1',
# 	'remote_procedure_args': [2, 3]
# }))

# print(arpcp.ARPCP.call('192.168.1.115', 7018, 'task', {
# 	'remote_procedure': 'divide',
# 	'remote_procedure_args': [6, 0]
# }))
# print(node1.procedures.divide(6, 0))


def calculater(a,b):
    return node1.procedures.async_multiple(a,b)

print(calculater(2,100))