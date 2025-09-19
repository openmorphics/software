from typing import Dict, List, Tuple; Event = Tuple[int, int, float, dict]
def trace_equivalent(a: Dict[str, List[Event]], b: Dict[str, List[Event]], tol_t: int=0, tol_v: float=1e-6):
    if a.keys()!=b.keys(): return False
    for k in a:
        if len(a[k])!=len(b[k]): return False
        for ea, eb in zip(a[k], b[k]):
            if abs(ea[0]-eb[0])>tol_t: return False
            if abs(ea[2]-eb[2])>tol_v: return False
    return True
