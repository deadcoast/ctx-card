"""
Pytest configuration and fixtures for CTX-CARD generator tests.
"""

from pathlib import Path
from typing import Dict, List, Tuple

import pytest

from ctxcard_gen.types import ModuleInfo, ScanResult, Symbol


@pytest.fixture
def sample_project_dir(tmp_path: Path) -> Path:
    """Create a sample project directory with Python files for testing."""
    project_dir = tmp_path / "sample_project"
    project_dir.mkdir()

    # Create main package
    main_pkg = project_dir / "main_pkg"
    main_pkg.mkdir()

    # Create __init__.py
    (main_pkg / "__init__.py").write_text(
        """
from .service import AuthService
from .models import User, UserCreds

__all__ = ["AuthService", "User", "UserCreds"]
"""
    )

    # Create service.py
    (main_pkg / "service.py").write_text(
        """
from typing import Optional
from .models import User, UserCreds
from .repository import UserRepository

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def login(self, creds: UserCreds) -> Optional[User]:
        \"\"\"
        Authenticate user with credentials.
        
        Requires: valid(creds)
        Ensures: user is authenticated
        \"\"\"
        user = self.user_repo.find_by_email(creds.email)
        if user and user.verify_password(creds.password):
            return user
        return None
    
    @classmethod
    def create(cls, user_repo: UserRepository) -> "AuthService":
        return cls(user_repo)
    
    @property
    def is_authenticated(self) -> bool:
        return hasattr(self, '_current_user')
"""
    )

    # Create models.py
    (main_pkg / "models.py").write_text(
        """
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel

@dataclass
class UserCreds:
    email: str
    password: str

class User(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool = True
    
    def verify_password(self, password: str) -> bool:
        # Simplified password verification
        return password == "correct_password"

class AuthError(Exception):
    \"\"\"Authentication error.\"\"\"
    pass

class ValidationError(Exception):
    \"\"\"Validation error.\"\"\"
    pass
"""
    )

    # Create repository.py
    (main_pkg / "repository.py").write_text(
        """
from typing import Optional, List
from .models import User

class UserRepository:
    def __init__(self):
        self.users: List[User] = []
    
    def find_by_email(self, email: str) -> Optional[User]:
        for user in self.users:
            if user.email == email:
                return user
        return None
    
    def save(self, user: User) -> User:
        self.users.append(user)
        return user
"""
    )

    # Create API module
    api_pkg = project_dir / "api"
    api_pkg.mkdir()

    (api_pkg / "__init__.py").write_text(
        """
from .routes import router

__all__ = ["router"]
"""
    )

    (api_pkg / "routes.py").write_text(
        """
from fastapi import APIRouter, HTTPException
from main_pkg.service import AuthService
from main_pkg.models import UserCreds, User

router = APIRouter()

@router.post("/login")
async def login(creds: UserCreds) -> User:
    auth_service = AuthService.create(None)
    user = auth_service.login(creds)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

@router.get("/users/{user_id}")
async def get_user(user_id: int) -> User:
    # This would normally fetch from database
    pass
"""
    )

    # Create utils module
    utils_pkg = project_dir / "utils"
    utils_pkg.mkdir()

    (utils_pkg / "__init__.py").write_text(
        """
from .helpers import format_name, validate_email

__all__ = ["format_name", "validate_email"]
"""
    )

    (utils_pkg / "helpers.py").write_text(
        """
import re
from typing import Optional

def format_name(first: str, last: str) -> str:
    return f"{first} {last}".strip()

def validate_email(email: str) -> Optional[str]:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    return None

def print_debug(message: str) -> None:
    print(f"DEBUG: {message}")  # This should trigger PX linting
"""
    )

    # Create test files
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()

    (tests_dir / "test_service.py").write_text(
        """
import pytest
from main_pkg.service import AuthService
from main_pkg.models import UserCreds, User

def test_login_success():
    # Test implementation
    pass

def test_login_failure():
    # Test implementation
    pass
"""
    )

    # Create a file with linting violations
    (project_dir / "bad_code.py").write_text(
        """
import os
import sys

# This should trigger PX linting violations
try:
    result = eval("2 + 2")
    print("Result:", result)
except:
    pass

def bad_function(items=[]):  # Mutable default
    return items

def another_bad_function():
    exec("print('hello')")
"""
    )

    return project_dir


@pytest.fixture
def sample_modules() -> Dict[str, ModuleInfo]:
    """Create sample module information for testing."""
    modules = {}

    # Module 1: auth/service.py
    mi1 = ModuleInfo(
        id=1, path="auth/service.py", dotted="auth.service", role_tags={"svc", "auth"}
    )
    mi1.symbols = [
        Symbol(mid=1, sid=1, kind="mod", name="service"),
        Symbol(mid=1, sid=1, kind="cls", name="AuthService"),
        Symbol(
            mid=1,
            sid=2,
            kind="fn",
            name="AuthService.login",
            signature="(UserCreds)->Optional[User]",
            raises=["AuthError"],
        ),
        Symbol(mid=1, sid=3, kind="prop", name="AuthService.is_authenticated"),
    ]
    mi1.fn_to_sid = {"AuthService.login": 2}
    mi1.prop_to_sid = {"AuthService.is_authenticated": 3}
    mi1.imports_paths = {"auth/models", "auth/repository"}
    mi1.dts = [("UserCreds", {"email": "str", "password": "str"})]
    mi1.errors = [("AuthError", "domain", "authentication failed")]
    mi1.routes = [(2, "POST", "/login", ["200", "401"])]
    mi1.px = [("forbid bare except", "error-handling")]
    modules["auth/service.py"] = mi1

    # Module 2: auth/models.py
    mi2 = ModuleInfo(
        id=2, path="auth/models.py", dotted="auth.models", role_tags={"dto"}
    )
    mi2.symbols = [
        Symbol(mid=2, sid=1, kind="mod", name="models"),
        Symbol(mid=2, sid=1, kind="cls", name="User"),
        Symbol(mid=2, sid=2, kind="cls", name="UserCreds"),
        Symbol(mid=2, sid=3, kind="cls", name="AuthError"),
    ]
    mi2.dts = [
        ("User", {"id": "int", "email": "str", "name": "str"}),
        ("UserCreds", {"email": "str", "password": "str"}),
    ]
    mi2.errors = [("AuthError", "domain", "authentication error")]
    modules["auth/models.py"] = mi2

    return modules


@pytest.fixture
def sample_scan_result(sample_modules) -> ScanResult:
    """Create sample scan result for testing."""
    return ScanResult(modules=sample_modules, langs=["py"])


@pytest.fixture
def sample_ctxcard_content() -> str:
    """Sample CTX-CARD content for testing."""
    return """ID: proj|test lang|py std|pep8 ts|20241201

AL: cfg=>Configuration
AL: svc=>Service
AL: repo=>Repository

NM: module | ^[a-z_]+$ | auth_service
NM: class  | ^[A-Z][A-Za-z0-9]+$ | AuthService
NM: func   | ^[a-z_]+$ | login
NM: var    | ^[a-z_]+$ | user_repo

MO: #1 | auth/service.py | {svc,auth}
MO: #2 | auth/models.py | {dto}

SY: #1.#0 | mod | service
SY: #1.#1 | cls | AuthService
SY: #1.#2 | fn | AuthService.login
SY: #2.#0 | mod | models
SY: #2.#1 | cls | User

SG: #1.#2 | (UserCreds)->Optional[User] !raises[AuthError]

DT: UserCreds | {email:str,password:str}
DT: User | {id:int,email:str,name:str}

ER: AuthError | domain | authentication error

ED: #1.#0 -> #2.#0 | imports

CN: repos never import svc
CN: async functions end with _async

RV: public functions have signatures & docstrings
"""


@pytest.fixture
def old_ctxcard_content() -> str:
    """Old CTX-CARD content for delta testing."""
    return """ID: proj|test lang|py std|pep8 ts|20241201

AL: cfg=>Configuration
AL: svc=>Service

NM: module | ^[a-z_]+$ | auth_service
NM: class  | ^[A-Z][A-Za-z0-9]+$ | AuthService

MO: #1 | auth/service.py | {svc,auth}

SY: #1.#0 | mod | service
SY: #1.#1 | cls | AuthService

CN: repos never import svc
"""
