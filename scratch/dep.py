
import logging
import sqlite3
from typing import Dict
from dependency_injector import containers, providers



from dependency_injector.wiring import Provide, inject

from deepsparse.dep_inj.container    import Container, UserService
from deepsparse.dep_inj.pipeline import Pipeline
from deepsparse.dep_inj.ops import Op


print(0)

op = [Op()]

p = Pipeline(op=op)
# breakpoint()
print(p.get_timer())
print(p.get_timer().timer())

# p = Pipeline()
# print(p.get_timer())

class MockOp(Op):
    
    def foo():
        mocker.patch("")
        ...
    
