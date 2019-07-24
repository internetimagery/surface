class _descriptor(object):
    def __get__(self, *_):
        raise RuntimeError("more like funtime error")


class Methods(object):

    ok_method = "ok"

    err_method = _descriptor()
