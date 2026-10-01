from __future__ import annotations
import hashlib
from dataclasses import dataclass, field, asdict

__all__ = [
    "UserProfile",
    "get_user_profile"
]

@dataclass(frozen = True)
class UserProfile:
    user_id_hash: str
    grade: str = ""
    department: str = ""
    role: str = ""
    audience: str = "all_staff"
    language: str = "en"
    
    def to_filter_dict(self) -> dict:
        return {
            "audience": self.audience,
            "grade": self.grade,
        }

class _MockHrisAdapter:
    """Deterministic mock: same user_id always returns the same profile."""
    _GRADES = ["A", "B", "C", "D", "E"]
    
    def fetch(self, user_id_hash: str) -> UserProfile:
        h = int(hashlib.sha256(user_id_hash.encode()).hexdigest(), 16)
        grade = self._GRADES[h % len(self._GRADES)]
        
        return UserProfile(
            user_id_hash=user_id_hash,
            grade=grade,
            department="operations",
            role="staff",
            audience="all_staff",
            language="en"
        )

_ADAPTER = _MockHrisAdapter()

def get_user_profile(user_id_hash: str) -> UserProfile:
    """Fetch the user profile for a given user_id_hash."""
    if not user_id_hash:
        return UserProfile(user_id_hash = "")
    return _ADAPTER.fetch(user_id_hash)