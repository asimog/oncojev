# OncoJev

OncoJev is an autonomous computational oncology research system for searching
large biological information spaces. A human supplies a broad direction; Director
allocates bounded questions and a fresh Researcher chooses how to investigate
The research thesis is whether typed semantic measurement, deterministic science
and selective reasoning improve useful discovery while preserving candidate recall.

## Documentation map

| Document | Read for |
| --- | --- |
| [Architecture](docs/ARCHITECTURE.md) | Durable structure and component authority |
| [Active plan](docs/IMPLEMENTATION_PLAN.md) | Next changes, status and acceptance |
| [Jev](docs/JEV.md) / [Capabilities](docs/CAPABILITIES.md) | Current subsystem contracts |
| [Frontend](docs/FRONTEND.md) | Current observability/read models |
| `src/*/README.md` | Current local implementation |

The completed F0-F6 archive and `docs/references/` preserve history and source
inputs. Read them only for a concrete historical/provenance question; they are not
normal working context or active instructions.

## Local development

Use the existing Windows environment for routine checks:

```powershell
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' <owning-test-file>
.venv/Scripts/python.exe -B scripts/check_architecture.py
git diff --check
```

The service uses the original SQLite database, default `var/oncojev.sqlite3`.
Linux-only scientific execution and confinement checks run directly in WSL2;
local-venv is the default scientific backend. Deployment is outside the current
scope. The [active plan](docs/IMPLEMENTATION_PLAN.md) owns acceptance and limits.
