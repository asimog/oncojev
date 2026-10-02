"""Versioned local execution proof, independent of scientific qualification.

Only direct WSL2 observations qualify. Historical target receipts remain readable
but cannot satisfy this contract. Missing/partial controls fail closed.
"""

LOCAL_VERIFICATION_VERSION = "local-verification-v1"
LOCAL_CHECKS = {
    "director_coder": ("filesystem", "credentials", "descendants"),
    "researcher_coder": ("filesystem", "credentials", "descendants"),
    "scientific_execution": ("filesystem", "credentials", "network", "process", "replay"),
    "resource_enforcement": ("process", "cpu", "memory", "disk", "downloads", "heavy_lease", "cancellation"),
}


def local_verification_passed(payload, application):
    """Check one complete receipt; controls cannot be combined across environments."""
    environment = payload.get("execution_environment", {})
    checks = payload.get("checks", {})
    if not isinstance(environment, dict) or not isinstance(checks, dict):
        return False
    return (
        payload.get("contract_version") == LOCAL_VERIFICATION_VERSION
        and payload.get("status") == "passed"
        and payload.get("application_identity") == application
        and payload.get("backend") == "local_venv"
        and environment.get("system") == "Linux"
        and environment.get("machine") == "x86_64"
        and isinstance(environment.get("release"), str)
        and "microsoft-standard-WSL2" in environment["release"]
        and all(isinstance(environment.get(key), str) and environment[key]
                for key in ("python", "executable"))
        and all(isinstance(checks.get(group), dict)
                and all(checks[group].get(name) is True for name in names)
                for group, names in LOCAL_CHECKS.items())
    )
