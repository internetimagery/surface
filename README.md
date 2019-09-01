
## Surface those API breaking changes!


Surface is a tool to facilitate exposing, inspecting and diffing the public API of your module.
Run it on your project to see at a glance what you are exposing to the world. Run it on your CI to prevent breaking API changes.

Example:

```python
# module test_module
public_var =  123
_private_var "123"
class PublicClass(object):
  def public_method(self, abc:int) -> bool:
    return self._private_method(abc)
  def _private_method(self, var):
    return var == 123
```
```sh
>>> surface dump test_module
```
```python
[test_module](0.0s)
class PublicClass:
  def public_method(
    a:int
  ) -> bool
public_var:int
```

The goal of this project is to assist in following semantic versioning. https://semver.org/

To that end, it can pick up on changes to the API and suggest (or check for on CI) version bumps. eg patch, minor, major

To do so, dump a copy of the old and new api to a temporary location and run a diff. Example:

```sh
# current "live" public API
>>> surface dump test_module -o /tmp/old_api.json
# add new WIP module to path and dump that API
>>> surface dump test_module -o /tmp/new_api.json
>>> surface compare /tmp/old_api.json /tmp/old_api.json
[major] Added Function: test_module.someExample
major
```

## Usage:

### Dump:

This subcommand will import and scan the provided api. Then output a representation of what it finds to where you specify.

* (--recurse) Walk through, and run on submodules.
* (--depth) Only traverse objects to this depth. (default 5)
* (--exclude-modules) Don't traverse imported modules. This (and the above) are helpful if the api is messy/large, and takes a long time to scan.
* (--all-filter) Respect `__all__` attrbiute. Treat the public api as though it were being imported with *.
* (--pythonpath PATH) Additions to the python path. These paths will be appened and used for lookup when running.
* (--output PATH) File (.json) in which to save the scanned info. Useful for comparisons later.
* (--git REPO) Alternative to --output. Will put the command in git mode. Changes will be stored in the git repo at the provided path (one will be created if it does not exist) based on the current commit hash and into the branch surface_API_store.

### Compare:

This subcommand will take two previously exported (above) files, and compare their changes. Outputting what it sees.

* (--bump VERSION) Instead of outputting a semantic level. It will instead take a version, and output the version with the level applied. eg --bump 1.2.3 instead of minor would become 1.3.0
* (--check LEVEL) Disallow this level (or higher). exit 1 if it exceeds the level. Useful for CI jobs to prevent breaking changes.
* (--git PATHS) Git mode. Treat 'old' and 'new' inputs as git identifiers (eg branches). Look for the corresponding data in repos at the provided paths, previously saved with the above gitmode.
* (--merge) Git mode. Instead of taking two identifiers and comparing. Take the commit at merge-base between the two. This is helpful to compare what changed since the branch diverged.

### Common options:

Common options that affect all subcommands.

* (--help) Display help message.
* (--quiet) Silence the reporting output.
* (--no-colour) Do not include ansii colours in output.
* (--rules) Print out a list of rules the tool adheres to.

There are some built in dev tools also.

* (--profile SORT) Run a profiler, and sort output by provided column.
* (--debug) Enable debug logging.
* (--pdb) Launch PDB on exceptions.


_This is very much a Work In Progress. Don't rely on it in production. (That said, feel free to test and report findings)._


Rough todo...
- [x] Get basic functionality up and running.
- [x] Handle recursive imports (if nessisary).
- [x] Collect Live typing information.
- [x] Collect annotation typing information.
- [x] Partial support for typing comments.
- [x] Partial support for docstring typing (google style only, currently)
- [ ] Search modules from bottom up. So "parent" relationships reflect module heirarchy, not traversal chain.
- [x] Utilize sigtools depth feature, to collect typing from comments on all arguments.
- [x] Improve typing comparison. Inspecting deeply nested types.
- [x] Provide features to store api output using git commits
- [x] Evaluate typing to ensure we get a live type, and correct paths etc
- [x] Move some of the cli utility stuff into its own submodule (public).
- [x] clean stuff up
- [x] When comparing types, check if they line up with an exposed alias.
- [x] use import hook to track import time properly (nice to have)
- [x] Compare Union correctly. Order of entires does not matter, and has an alias: Optional[something]
- [x] Same thing with NoneType and None. Both are equal.
- [x] Unknown have a type field for comparisons. Instead of full text comparison.
- [ ] More and more and more tests.
