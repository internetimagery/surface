
## Bring your API to the surface!

_This is very much a Work In Progress. Don't use it in production (yet)._

The goal of this project is to pull out the exposed public api from a given module.

The result of which can be used for operations like comparisons. Helping determine semantic versioning, etc.

Such comparisons can also be useful as CI jobs on rapidly changing projects, where you cannot afford to accidently bump the Major version, for instance.

Sky is the limit, but work still needs to be done!

Rough todo...
[x] Get basic functionality up and running.
[ ] Handle recursive imports (if nessisary).
[x] Collect Live typing information from import.
[x] Collect annotation typing information from python3
[ ] Collect typing comments.
[ ] Reduce dependency on sigtools. It's useful but might be overkill here.
[ ] More and more and more tests.
