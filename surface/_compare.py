""" Compare two API's """


# Semantic types
PATCH = "patch"
MINOR = "minor"
MAJOR = "major"


def compare(api_old, api_new): # type: (Sequence[Any], Sequence[Any]) -> Dict[str, str]
    """ Compare two API's, and return result """
    changes = {
        PATCH: check_patch(api_old, api_new),
        MINOR: check_minor(api_old, api_new),
        MAJOR: check_major(api_old, api_new),
    }
    return changes


def check_patch(api_old, api_new):
    return


def check_minor(api_old, api_new):
    return


def check_major(api_old, api_new):
    return
