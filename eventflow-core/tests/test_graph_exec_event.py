import unittest; from eventflow_core.eir.ops import *; from eventflow_core.eir.graph import *; from eventflow_core.runtime.exec import run_event_mode
class TestGraph(unittest.TestCase):
  def test_chain(self):
    def stim(): yield from [(t*10**6,0,1.0,{}) for t in (1,2,3)]
    g=EIRGraph(); g.add_node("n0",ExpSynapse("s0").as_op()); g.add_node("n1",LIFNeuron("l1").as_op()); g.connect("n0","post","n1","in")
    out=run_event_mode(g,inputs={"n0":stim()})
    self.assertGreater(len(out["n1"]), 0)
