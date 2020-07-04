class _descriptor(object):
    def __get__(self, *_):
        from test_mod_basic.cycleB import CycleB

        return CycleB


class CycleA(object):
    cycle = _descriptor()


import surface.dump._export
