import importlib

from pyhike import TrailBlazer

from surface.dump._traversal import RepresentationBuilder
from surface.dump._export import export_stubs


class Exporter(object):

    def __init__(self, modules=None, files=None, directories=None):
        # type: (Optional[Sequence[str]], Optional[Sequence[str]], Optional[Sequence[str]]) -> None
        self._modules = modules or []
        self._files = files or []
        self._directories = directories or []
    
    def export(self, directory):
        # type: (str) -> None
        builder = RepresentationBuilder()
        traveler = TrailBlazer(builder)
        for module in self._modules:
            traveler.roam_module(module)
        for file_ in self._files:
            traveler.roam_file(file_)
        for directory_ in self._directories:
            traveler.roam_directory(directory_)
        traveler.hike()
        export_stubs(builder.get_representation(), directory)
