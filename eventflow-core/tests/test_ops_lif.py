import unittest; from eventflow_core.eir.ops import step_lif, LIFState
class TestOps(unittest.TestCase):
  def test_lif_spikes(self):
    st=LIFState(tau_m_ns=10*10**6,v_th=.9,v_reset=0,r_m=1,refractory_ns=2*10**6)
    inp=[(t*10**6,0,1,{}) for t in (1,2,3)]; out=list(step_lif(iter(inp), st))
    self.assertEqual(len(out), 1); self.assertAlmostEqual(out[0][0], 1_000_000, delta=1)
