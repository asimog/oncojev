from oncojev.capabilities.models import ScientificCapability
class ScientificCapabilityRegistry:
 def __init__(self,items:tuple[ScientificCapability,...]):self._items=items
 def search(self,need:str)->tuple[ScientificCapability,...]:
  return tuple(x for x in self._items if set(need.lower().split()) & set((x.name+' '+x.description).lower().split()))
