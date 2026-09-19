from dataclasses import dataclass,field
from typing import Callable,Optional

@dataclass
class Tweak:
    id:str
    name:str
    category:str
    description:str
    risk:str="SAFE"
    recommended:bool=False
    reversible:bool=True
    requires_admin:bool=False
    restart:str="None"
    check:Optional[Callable[[],bool]]=None
    apply:Optional[Callable[[],str]]=None
    rollback:Optional[Callable[[],str]]=None
    metadata:dict=field(default_factory=dict)
