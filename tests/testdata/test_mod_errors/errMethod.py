class Methods(object):

    ok_method = "ok"

    @property
    def err_method(self):
        raise RuntimeError("more like funtime error")
