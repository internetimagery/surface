
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

_This is very much a Work In Progress. Don't rely on it in production. (That said, feel free to test and report findings)._


Rough todo...
- [x] Get basic functionality up and running.
- [x] Handle recursive imports (if nessisary).
- [x] Collect Live typing information.
- [x] Collect annotation typing information.
- [x] Partial support for typing comments.
- [x] Partial support for docstring typing (google style only, currently)
- [ ] Reduce dependency on sigtools. It's useful but might be overkill here.
- [ ] More and more and more tests.
