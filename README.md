## Perform checks listed in patches/ folder

### Script could be executed outside of the project.
Example:

```
(venv) $ ./patch_checker/patch_checker.py globalai-infra/p04-infra/vendor/infra-controller
globalai-infra/p04-infra/vendor/infra-controller: release-v2.2_lenovo_dell 1c57b28b (HEAD -> release-v2.2_lenovo_dell, origin/release-v2.2_lenovo_dell)
OK. All patches in place
```

### Requires:
- git
- python pyaml

### Versioning
Yes, line numbers may change across different releases and several patches may be invalid or you need to add new related to a release.
This is why this repo has branches matching the product.
Checkout your release to get list of checks matching your product release
