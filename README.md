
## Bring your API to the surface!

_This is very much a Work In Progress. Don't rely on it in production. (That said, feel free to test and report findings)._

The goal of this project is to pull out the exposed public api from a given module, and check against it.

https://semver.org/

The result of which can be used for operations like comparisons. Helping determine semantic versioning, etc.

Such comparisons can also be useful as CI jobs on rapidly changing projects, where you cannot afford to accidently bump the Major version, for instance.

Sky is the limit, but work still needs to be done!

Rough todo...
- [x] Get basic functionality up and running.
- [x] Handle recursive imports (if nessisary).
- [x] Collect Live typing information from import.
- [x] Collect annotation typing information from python3
- [ ] Try use typing comments.
- [ ] Try use pyi files if present.
- [ ] Normalize typing to be absolute paths or relative paths only.
- [ ] Reduce dependency on sigtools. It's useful but might be overkill here.
- [ ] More and more and more tests.
