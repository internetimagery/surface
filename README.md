
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
>>> surface dump test_module -o /tmp/new_api.json -p /path/to/dev/module -b 1.2.3
>>> surface compare /tmp/old_api.json /tmp/old_api.json
Added Function: test_module.someExample
2.0.0
```

Another option is to create snapshots on CI for every push, and compare against them. This is useful if it's hard to recreate an environment later on, and so cannot reliably go back and get a base to compare API changes from.

The --git flag exists in both "dump" and "compare" modes.

In "dump", it will get the current commit from the working directory, and store the API file within the provided directory, with the commit hash as identifier. eg:

```sh
>>> surface dump test_module --git /path/to/storage
```

In "compare" mode, it will treat the old / new arguments as branch names instead of filepaths. It will then (using the repo in the current directory) find the commit with a common base between the two, and use that as the origin.

The argument takes multiple paths separated by (,:;) characters. The commit will be searched for in all these paths eg:

```sh
>>> surface compare master develop --git /path/to/storage:/path/to/more/storage:/path/to/maybe/local/storage
```

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
- [ ] Look into xml as alternate storage to json. Especially useful with comments in a header.
- [x] Move some of the cli utility stuff into its own submodule (public).
- [x] clean stuff up
- [ ] When comparing types, check if they line up with an exposed alias.
- [ ] use import hook to track import time properly (nice to have)
- [ ] API.Unknown have a type field for comparisons. Instead of full text comparison.
- [ ] More and more and more tests.
