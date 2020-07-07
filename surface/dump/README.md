
# Export public facing api

Dump the public facing api into stub files.

Useful for autocomplete, typechecking and comparing the difference between two sets of stubs.

In the case of surface we handle the latter to expose changes to the user where it may not have been obvious, and
potentially to also restrict changes (ie no "major" breaking changes) in a CI environment.
Depending on the projects needs.

## API

This module exposes an **Exporter** class. To use in order to generate a view into the public api and also create stub files.

* **Exporter**(modules=None, files=None, directories=None): All options in which to export. 
* **Exporter.get_representation**(): Return a representation of the public facing api.
* **Exporter.export**(directory): Generate stub files in the path provided. Return a representation of the public facing api.