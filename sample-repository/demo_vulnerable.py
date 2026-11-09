"""DEMONSTRATION FILE - intentionally insecure. Never execute in production.

Used as a fixture to verify that the CodeGuard AI analyzer reports real issues.
"""
import hashlib
import os
import subprocess

# Hardcoded AWS access key (CWE-798)
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# Hardcoded password (CWE-798)
DATABASE_PASSWORD = "SuperSecret123"


def run_backup(path: str) -> None:
    # Command injection risk (CWE-78)
    os.system("tar -czf backup.tar.gz " + path)


def run_command(user_input: str) -> None:
    # shell=True command injection risk (CWE-78)
    subprocess.run("echo " + user_input, shell=True)


def calculate(value: str) -> int:
    # eval() on untrusted input (CWE-95)
    return eval(value)


def weak_hash(data: bytes) -> str:
    # Weak hash algorithm (CWE-327)
    return hashlib.md5(data).hexdigest()


def risky():
    try:
        return 1 / 0
    except:
        # Bare except swallows everything (code quality)
        return None


def check_flag(flag):
    # Identity comparison with a literal
    if flag is True:
        return "enabled"
    return "disabled"
