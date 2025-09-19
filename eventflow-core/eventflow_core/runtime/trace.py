import json
from typing import Dict, List, Tuple; Event = Tuple[int,int,float,dict]
def record(p: str, o: Dict[str, List[Event]]): (lambda f:json.dump({k:v for k,v in o.items()},f))(open(p,"w")); return p
def load(p: str) -> Dict[str, List[Event]]: return json.load(open(p))
