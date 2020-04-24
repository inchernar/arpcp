#!/usr/bin/env python3

import arpcp

node1 = arpcp.RemoteNode('192.168.1.115')
# print(node1.procedures)

# print(node1.procedures.func1(2, 1))
print(node1.procedures.multiple(2.02, 5.823))

# print(dir(node1.procedures))

# print(node1.procedures.async_func1())