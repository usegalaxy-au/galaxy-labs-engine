This task requires restructuring the package layout slightly and changing how the imports work.

Right now, the setup installs the contents of `app/` as **top-level packages**, because we’ve told setuptools:

```toml
[tool.setuptools.package-dir]
"" = "app"
```

That makes `utils`, `labs`, etc., appear directly under `site-packages`, since they’re top-level under `app/`.

---

### Correct Approach

We want all the internal modules (like `utils` and `labs`) to live under a single namespace — e.g. `labs_engine`.
To achieve that:

#### 1. Restructure the repository

Move everything under a proper package directory:

```
.
├── app/
│   ├── labs_engine/
│   │   ├── __init__.py
│   │   ├── utils/
│   │   ├── labs/
│   │   ├── cli.py
│   │   └── ...
│   ├── manage.py
│   ├── db.sqlite3
│   └── ...
```

So that the Python package hierarchy is `labs_engine.utils`, `labs_engine.labs`, etc.

---

#### 2. Update `pyproject.toml`

```toml
[tool.setuptools]
packages = { find = { where = ["app"] } }

[tool.setuptools.package-dir]
"" = "app"

[project.scripts]
labs-engine = "labs_engine.cli:main"
```

Now setuptools will find `labs_engine` under `app/` and install it properly under that namespace.

---

#### 3. Fix imports in the Django project

You’ll need to change internal imports to the new namespace.
For example:

```python
# old
from utils import blah
from labs.models import Sample

# new
from labs_engine.utils import blah
from labs_engine.labs.models import Sample
```

---

#### 4. Run tests

Check .vscode/launch.json to see how unit tests should be run. Run them, and fix any bugs they raise.

---

#### 5. Test installation

In a disposable venv:

- Check `pip install --force .` runs ok
- Check that `labs-engine serve` runs without error - you should run this in /home/cameron/dev/galaxy/galaxy-labs-engine/app/labs/example_labs/simple which contains example content that can be served.
