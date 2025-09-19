class Watermark:
    def __init__(self): self._wm=-1
    def advance(self, t:int): self._wm = max(self._wm, t)
    def value(self)->int: return self._wm
