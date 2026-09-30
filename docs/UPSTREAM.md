# Upstream references

`.upstream/` is pinned reference material, not a dependency directory. Application runtime must never import it. Normal searches, indexing, linting, type checks, tests, and repository summaries exclude it.

For a concrete question only, inspect `.upstream/manifest.yaml`, select one repository and the smallest relevant path, then stop. The manifest records direct architectural and scientific references; transitive dependencies remain ordinary package-manager dependencies.
