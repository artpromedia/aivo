from enum import Enum

class ModerationResult(Enum):
    PASSED = "passed"
    BLOCKED = "blocked"
    ERROR = "error"

print("Testing enum:")
print(f"PASSED: {ModerationResult.PASSED}")
print(f"BLOCKED: {ModerationResult.BLOCKED}")
print(f"ERROR: {ModerationResult.ERROR}")
print("Enum works correctly!")
