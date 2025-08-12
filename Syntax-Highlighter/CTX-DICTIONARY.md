# CTX-CARD VSCode Syntax Highlighting Specification

## Overview

This document defines the VSCode TextMate grammar for CTX-CARD (`.ctx`) files. CTX-CARD is a prefix-free, information-dense codebook format designed for AI agent context and codebase documentation.

## File Extension

- **Primary**: `.ctx`
- **Fallback**: `.ctxc` (if `.ctx` conflicts with other applications)

## Grammar Structure

### 1. Core Tags (2-4 character identifiers)

#### **Global Identity Tags**

- `ID:` - Project identity and metadata
- `AL:` - Alias table (prefix-free abbreviations)
- `NM:` - Naming grammar with regex patterns

#### **Configuration and Environment Tags**

- `DEPS:` - External dependencies and versions
- `ENV:` - Environment variables and configuration
- `SEC:` - Security constraints and permissions

#### **Index and Structure Tags**

- `MO:` - Module index with role tags
- `SY:` - Symbol index within modules
- `SG:` - Function signatures with raises
- `MD:` - Method modifiers (staticmethod, classmethod, property, descriptor)

#### **Relationship Tags**

- `ED:` - Edge relationships (imports/calls)
- `EVT:` - Event relationships and handlers
- `TY:` - Type signature schema (optional)

#### **Semantic Tags**

- `IN:` - Invariants/contracts (Hoare-style)
- `CN:` - Coding conventions (micro-rules)
- `ER:` - Error taxonomy
- `IO:` - I/O contracts (API endpoints)
- `DT:` - Data shapes (schemata)
- `TK:` - Token/enum keysets
- `ASYNC:` - Asynchronous patterns and promises

#### **Policy and Review Tags**

- `PX:` - Prohibited/allowed patterns
- `EX:` - Canonical examples
- `RV:` - Review focus (checklists)
- `DELTA:` - Delta changes since timestamp

### 2. Syntax Patterns

#### **Tag Patterns**

```regex
^(ID|AL|NM|DEPS|ENV|SEC|MO|SY|SG|MD|ED|EVT|TY|IN|CN|ER|IO|DT|TK|ASYNC|PX|EX|RV|DELTA):
```

#### **Index References**

```regex
#\d+\.\d+
```

#### **Role Tags**

```regex
\{[^}]+\}
```

#### **Arrow Relationships**

```regex
->|⇒
```

#### **Pipe Separators**

```regex
\|
```

#### **Alias Definitions**

```regex
=>|→
```

#### **Regex Patterns**

```regex
\^[^$]+\$
```

#### **Function Signatures**

```regex
\([^)]*\)->[^!]*!?raises?\[[^\]]*\]
```

#### **Comments**

```regex
#.*$
```

## VSCode TextMate Grammar

### Grammar File: `ctx.tmLanguage.json`

```json
{
  "name": "CTX-CARD",
  "scopeName": "source.ctx",
  "fileTypes": ["ctx", "ctxc"],
  "patterns": [
    {
      "include": "#comments"
    },
    {
      "include": "#tags"
    },
    {
      "include": "#indices"
    },
    {
      "include": "#relationships"
    },
    {
      "include": "#signatures"
    },
    {
      "include": "#patterns"
    }
  ],
  "repository": {
    "comments": {
      "patterns": [
        {
          "name": "comment.line.number-sign.ctx",
          "match": "#.*$"
        }
      ]
    },
    "tags": {
      "patterns": [
        {
          "name": "keyword.control.ctx",
          "match": "^(ID|AL|NM|DEPS|ENV|SEC|MO|SY|SG|MD|ED|EVT|TY|IN|CN|ER|IO|DT|TK|ASYNC|PX|EX|RV|DELTA):"
        }
      ]
    },
    "indices": {
      "patterns": [
        {
          "name": "constant.numeric.ctx",
          "match": "#\\d+\\.\\d+"
        },
        {
          "name": "constant.numeric.ctx",
          "match": "#\\d+"
        }
      ]
    },
    "relationships": {
      "patterns": [
        {
          "name": "keyword.operator.arrow.ctx",
          "match": "->"
        },
        {
          "name": "keyword.operator.arrow.ctx",
          "match": "⇒"
        },
        {
          "name": "keyword.operator.pipe.ctx",
          "match": "\\|"
        },
        {
          "name": "keyword.operator.alias.ctx",
          "match": "=>"
        },
        {
          "name": "keyword.operator.alias.ctx",
          "match": "→"
        }
      ]
    },
    "signatures": {
      "patterns": [
        {
          "name": "meta.function.signature.ctx",
          "match": "\\([^)]*\\)->[^!]*!?raises?\\[[^\\]]*\\]"
        },
        {
          "name": "meta.function.signature.ctx",
          "match": "\\([^)]*\\)->[^!]*"
        }
      ]
    },
    "patterns": {
      "patterns": [
        {
          "name": "string.quoted.role-tags.ctx",
          "match": "\\{[^}]+\\}"
        },
        {
          "name": "string.regex.ctx",
          "match": "\\^[^$]+\\$"
        },
        {
          "name": "string.quoted.path.ctx",
          "match": "[a-zA-Z0-9_/.-]+\\.(py|js|ts|go|java|cpp|h|hpp)$"
        }
      ]
    }
  }
}
```

## Color Theme Integration

### **Semantic Color Mapping**

#### **Tags (Keywords)**

- **Color**: `#569CD6` (Blue)
- **Scope**: `keyword.control.ctx`
- **Purpose**: Highlight CTX-CARD tag identifiers

#### **Indices (Numbers)**

- **Color**: `#B5CEA8` (Light Green)
- **Scope**: `constant.numeric.ctx`
- **Purpose**: Highlight module and symbol indices

#### **Relationships (Operators)**

- **Color**: `#D4D4D4` (Light Gray)
- **Scope**: `keyword.operator.*.ctx`
- **Purpose**: Highlight arrows, pipes, and aliases

#### **Role Tags (Strings)**

- **Color**: `#CE9178` (Orange)
- **Scope**: `string.quoted.role-tags.ctx`
- **Purpose**: Highlight role tag sets

#### **Function Signatures (Meta)**

- **Color**: `#C586C0` (Purple)
- **Scope**: `meta.function.signature.ctx`
- **Purpose**: Highlight function signatures and raises

#### **Regex Patterns (Strings)**

- **Color**: `#D7BA7D` (Yellow)
- **Scope**: `string.regex.ctx`
- **Purpose**: Highlight naming grammar patterns

#### **Comments** Pattern

- **Color**: `#6A9955` (Green)
- **Scope**: `comment.line.number-sign.ctx`
- **Purpose**: Highlight documentation comments

## Language Features

### **1. Syntax Validation**

- Validate tag format (2-4 characters + colon)
- Check index reference format (#mid.sid)
- Verify role tag format ({tag1,tag2})
- Validate function signature syntax

### **2. IntelliSense Support**

- Tag completion for all CTX-CARD tags
- Index reference completion
- Role tag suggestions
- Function signature templates

### **3. Error Detection**

- Invalid tag identifiers
- Malformed index references
- Unmatched braces in role tags
- Invalid function signatures

### **4. Folding Support**

- Fold by tag sections
- Fold large role tag lists
- Fold function signature blocks

## Implementation Notes

### **File Association**

```json
{
  "fileAssociations": [
    {
      "pattern": "*.ctx",
      "scheme": "file"
    },
    {
      "pattern": "*.ctxc",
      "scheme": "file"
    }
  ]
}
```

### **Language Configuration**

```json
{
  "comments": {
    "lineComment": "#"
  },
  "brackets": [
    ["{", "}"],
    ["[", "]"],
    ["(", ")"]
  ],
  "autoClosingPairs": [
    { "open": "{", "close": "}" },
    { "open": "[", "close": "]" },
    { "open": "(", "close": ")" }
  ],
  "surroundingPairs": [
    ["{", "}"],
    ["[", "]"],
    ["(", ")"]
  ]
}
```

## Testing Examples

### **Basic CTX-CARD File**

```ctx
ID: proj|myProject lang|py std|pep8 ts|20241201
AL: cfg=>Configuration svc=>Service repo=>Repository
NM: module | ^[a-z_]+$ | auth_service
NM: class  | ^[A-Z][A-Za-z0-9]+$ | AuthService
MO: #1 | auth/service.py | {svc,auth}
SY: #1.#1 | cls | AuthService
SY: #1.#2 | fn  | login
SG: #1.#2 | (UserCreds)->AuthToken !raises[AuthError]
ED: #1.#2 -> #2.#1 | calls
IN: login ⇒ requires(valid(creds)) ∧ ensures(token.exp>now)
CN: async fn end with _async
PX: forbid bare except | error-handling
```

### **Complex Example**

```ctx
# CTX-CARD for complex project
ID: proj|complexApp lang|py,ts std|pep8,eslint ts|20241201

AL: cfg=>Configuration svc=>Service repo=>Repository dto=>DataTransferObject
AL: uc=>UseCase http=>HTTP db=>Database jwt=>JWT api=>API

DEPS: requests | external | HTTP client library
DEPS: pandas | external | Data analysis library
DEPS: fastapi | external | Web framework
ENV: auth_service | environment | config
ENV: database_url | environment | config
SEC: AuthService | authentication | required
SEC: SecurityMiddleware | authorization | required

NM: module | ^[a-z_]+$ | auth_service
NM: class  | ^[A-Z][A-Za-z0-9]+$ | AuthService
NM: func   | ^[a-z_]+$ | issue_token
NM: var    | ^[a-z_]+$ | user_repo

MO: #1 | auth/service.py | {svc,auth,api}
MO: #2 | auth/repository.py | {repo,auth,db}
MO: #3 | auth/dto.py | {dto,auth}

SY: #1.#1 | cls | AuthService
SY: #1.#2 | fn  | login
SY: #1.#3 | fn  | refresh_token
SY: #2.#1 | cls | UserRepository
SY: #3.#1 | cls | UserCreds
SY: #3.#2 | cls | AuthToken

SG: #1.#2 | (UserCreds)->AuthToken !raises[AuthError,ValidationError]
SG: #1.#3 | (str)->AuthToken !raises[AuthError]
SG: #2.#1 | (db:Database)->None

MD: #1.#2 | {classmethod}
MD: #2.#1 | {singleton}

ED: #1.#2 -> #2.#1 | uses:repo
ED: #1.#2 -> #3.#1 | accepts:dto
ED: #1.#2 -> #3.#2 | returns:dto
ED: #1.#3 -> #2.#1 | uses:repo

EVT: #1.#2 | event | login_event
EVT: #1.#3 | event | token_refresh_event

ASYNC: #1.#2 | async | login_async
ASYNC: #1.#3 | async | refresh_token_async

DT: UserCreds | {email:str,password:str,remember:bool}
DT: AuthToken | {jwt:str,exp:datetime,user_id:int}

TK: Role | {admin,staff,viewer,guest}
TK: Status | {active,inactive,suspended}

ER: AuthError | domain | authentication failure
ER: ValidationError | domain | input validation failure

IN: login ⇒ requires(valid(creds)) ∧ ensures(token.exp>now)
IN: refresh_token ⇒ requires(valid(jwt)) ∧ ensures(new_token.exp>old_token.exp)

CN: async fn end with _async
CN: repos never import svc
CN: all public fn have type hints

IO: POST /v1/login | UserCreds | AuthToken | 200,401,422
IO: POST /v1/refresh | str | AuthToken | 200,401

PX: forbid bare except | error-handling
PX: forbid global state in svc | concurrency
PX: forbid print() in production | logging

EX: var(repo) => user_repo (not usersRepo)
EX: fn(async) => login_async (not loginAsync)

RV: Check invariants (IN) on public fn
RV: Verify error handling (ER) coverage
RV: Validate naming conventions (NM)
```

## Future Enhancements

### **Language Server Protocol (LSP)**

- Semantic token support
- Code actions for tag generation
- Validation and error reporting
- Auto-completion for indices

### **Advanced Features**

- CTX-CARD diff highlighting
- Delta section folding
- Cross-reference navigation
- Schema validation

### **Integration Features**

- GitHub syntax highlighting
- Documentation site support
- IDE plugin compatibility
- Custom theme support
