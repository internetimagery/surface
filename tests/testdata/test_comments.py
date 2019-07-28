# fmt: off
def func1(a, b, c):  # type: (int, str, Dict[str, List[str]]) -> None
    return

# Assignment comment types not supported yet
var = 123 # type: int

def func2(

): # type: () -> None
    pass

def func3(
    a, # type: int
    b, # type: List[str]
    c = None # type: Dict[str, List[str]]
        ):
                # type: (...) -> None
    return
