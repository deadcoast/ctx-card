# **CTX-CARD** (Context Card)

_A prefix-free, information-dense codebook_ + _edge list_ + _naming grammar_. It’s deterministic, easy to diff, and cheap to load.

---

## CTX-CARD v1 (spec)

**File naming:** `CTXCARD.md` at repo root (and optionally `CTXCARD.<pkg>.md` per package).

### General rules

- ASCII only. One item per line. No prose outside comments.
- Lines start with a **2–4 char tag** → colon → payload.
- Identifiers are **indexed** to compress references.
- Abbreviations are **prefix-free** (no alias is a prefix of another).

### Tags (minimal vocabulary)

- `ID:` **Global identity** ⇒ `proj | lang | std | ts`
  - `proj` project slug; `lang` primary language(s); `std` standards (e.g., pep8); `ts` semantic timestamp (YYYYMMDD).
- `AL:` **Alias table** ⇒ `k => value` (prefix-free, reused everywhere)
  - e.g., `AL: cfg=>Configuration, svc=>Service, repo=>Repository`
- `NM:` **Naming grammar (regex)** ⇒ `scope | pattern | example`
  - e.g., `NM: func | ^[a-z][a-z0-9_]*$ | get_user_token`
- `TY:` **Type signature schema** ⇒ `kind | name | sig`
  - e.g., `TY: fn | AuthService.login | (UserCreds)->AuthToken !raises[AuthError]`
- `TK:` **Token/enum keysets** ⇒ `name | {k1,k2,...}`
  - e.g., `TK: Role | {admin,staff,viewer}`
- `MO:` **Module index** ⇒ `#id | path | role-tags`
  - e.g., `MO: #3 | auth/service.py | {svc,auth,api}`
- `SY:` **Symbol index (within module)** ⇒ `#mid.#sid | kind | name`
  - e.g., `SY: #3.#1 | cls | AuthService`
- `SG:` **Signature for symbol** ⇒ `#mid.#sid | signature` (uses `TY` schema)
  - e.g., `SG: #3.#2 | (UserCreds)->AuthToken`
- `ED:** **Edges (deps & calls)** ⇒`src -> dst | reason-tag\`
  - e.g., `ED: #3.#2 -> #5.#1 | uses:repo`
- `IN:` **Invariants / contracts** ⇒ short Hoare-style
  - e.g., `IN: login ⇒ requires(valid(creds)) ∧ ensures(token.role∈Role)`
- `CN:` **Conventions (micro-rules)** ⇒ bullet-ish constraints
  - e.g., `CN: All async fn end with _async; HTTP funcs return Result[T,HTTPError]`
- `ER:` **Error taxonomy** ⇒ `Name | category | meaning`
  - e.g., `ER: AuthError | domain | invalid credentials`
- `IO:` **I/O contracts** ⇒ `endpoint | in | out | codes`
  - e.g., `IO: POST /v1/login | UserCreds | AuthToken | 200,401,429`
- `DT:` **Data shapes (schemata)** ⇒ `Name | fields`
  - e.g., `DT: UserCreds | {email:str, pwd:secret(>=12)}`
- `PX:` **Prohibited/allowed patterns** ⇒ `rule | reason`
  - e.g., `PX: forbid global state in svc | concurrency`
- `EX:` **Examples (1-liners)** ⇒ canonical name spellings
  - e.g., `EX: repo var => user_repo (not usersRepo)`
- `RV:` **Review focus** ⇒ terse checklists
  - e.g., `RV: Public fns documented; No bare except`
- `Δ:` **Delta since ts** ⇒ same tags, limited to changes (diff card)

> Each tag maps to a distinct “latent” an agent needs: lexicon (AL), morphology (NM), types (TY/DT), topology (MO/SY/ED), semantics (IN/IO/ER), policy (CN/PX/RV). This covers structure with \~O(n) lines and low-entropy tokens.

---

## Worked example (Python, SRP-style)

```yaml
ID: proj|milkBottle lang|py std|pep8 ts|20250808

AL: cfg=>Configuration svc=>Service repo=>Repository dto=>DataTransferObject
AL: uc=>UseCase http=>HTTP db=>Database jwt=>JWT

NM: module | ^[a-z_]+$ | auth_service
NM: class  | ^[A-Z][A-Za-z0-9]+$ | AuthService
NM: func   | ^[a-z_]+$ | issue_token
NM: var    | ^[a-z_]+$ | user_repo

DT: UserCreds | {email:str, pwd:secret(>=12)}
DT: AuthToken | {jwt:str, exp:utc}

TK: Role | {admin,staff,viewer}

MO: #1 | auth/service.py | {svc,auth}
MO: #2 | auth/repository.py | {repo,auth}
MO: #3 | auth/dto.py | {dto,auth}

SY: #1.#1 | cls | AuthService
SY: #1.#2 | fn  | login
SY: #2.#1 | cls | UserRepository
SY: #3.#1 | cls | UserCreds
SY: #3.#2 | cls | AuthToken

TY: fn | AuthService.login | (UserCreds)->AuthToken !raises[AuthError]
SG: #1.#2 | (UserCreds)->AuthToken !raises[AuthError]

ED: #1.#2 -> #2.#1 | uses:repo
ED: #1.#2 -> #3.#2 | returns:dto

ER: AuthError | domain | bad credentials
IN: login ⇒ requires(valid(creds)) ∧ ensures(token.exp>now)

CN: async fn end with _async
CN: repos never import svc

IO: POST /v1/login | UserCreds | AuthToken | 200,401,429

EX: var(repo) => user_repo
RV: Check invariants (IN) on public fn
```

This is \~30 lines and gives the agent:

- Allowed names (regex) and their _shape_
- Types and DTOs with minimal fields
- Module and symbol indices (stable handles)
- Call graph edges as cheap `src->dst`
- Contract snippets (pre/post)

---

## Breakdown (brief mathy sanity)

- **Prefix-free aliases** (`AL`) → Kraft–McMillan-style: decodable without ambiguity, minimizing collisions in the agent’s latent “dictionary.” Less perplexity = fewer tokens needed to “pin” concepts.
- **Regex morphology** (`NM`) collapses a _class_ of valid strings into a few symbols. One regex can stand in for hundreds of filenames/functions.
- **Indices** (`#m.#s`) replace long paths/symbols: each edge line becomes \~≤25 chars instead of 60–120.
- **Edge list** (`ED`) is O(E) with tiny constants; for most SRP codebases E≈N..1.5N. Much cheaper than trees.
- **Information packing**: Each tag line carries orthogonal features; mutual information between tags is low (by design), reducing redundancy and prompt tokens.

---

## Authoring guidance

- Keep **CTX-CARD** under \~200 lines per repo; split by package if needed.
- On each PR, maintain a **Δ** section (just the changed lines) to keep diffs minuscule for agent refresh.
- Never duplicate names: define once (`SY`/`TY`), reference by index (`SG`/`ED`).
- Prefer **sets/tags** over prose: `{svc,auth,api}` is enough for role intent.

---

## Drop-in template

```yaml
ID: proj|<slug> lang|<lang[,lang]> std|<style> ts|<YYYYMMDD>

# Aliases (prefix-free):
AL: <k1>=> <value1>
AL: <k2>=> <value2>

# Naming grammar:
NM: module | <regex> | <example>
NM: class  | <regex> | <example>
NM: func   | <regex> | <example>
NM: var    | <regex> | <example>

# Data & tokens:
DT: <Name> | {<field>:<type>[,<rule>], ...}
TK: <Name> | {a,b,c}

# Modules:
MO: #<m> | <path> | {<tags>}

# Symbols:
SY: #<m>.#<s> | <kind> | <Name>
SG: #<m>.#<s> | (<Args>)-><Ret> [!raises[...]][mods...]

# Edges:
ED: #<m>.#<s> -> #<m'>.#<s'> | <reason-tag>

# Contracts & policy:
IN: <predicate>
ER: <Name> | <category> | <meaning>
CN: <rule>
PX: <rule> | <reason>
IO: <verb path> | <in> | <out> | <codes>

# Examples / review:
EX: <micro example>
RV: <checklist item>

# Delta (since ts):
Δ: <tag-lines copied here, only what changed>
```

---

## CTX-CARD: Compact Context Encoding for Codebase Understanding

```yaml
# CTX-CARD: Compact Context Encoding for Codebase Understanding
# Purpose: Provide minimal-token, high-information structural + semantic map of a codebase.
# Goal: Enable precise reasoning over naming, types, relationships, and rules.

## 1. GENERAL PRINCIPLES
- All info stored as tagged, one-line entries.
- Tags are prefix-free 2–4 chars → colon → payload.
- Identifiers are indexed (#m.#s) for compact references.
- Aliases & regex rules compress vocabulary.
- No prose outside comments (#).
- Use sets `{}` for tags/roles instead of sentences.
- Maintain ≤200 lines per repo; split into multiple CTX-CARD files if needed.
- File exclusion via `.ctxignore` patterns for focused analysis.

## 2. TAG DEFINITIONS

ID: Global identity → proj|<slug> lang|<lang[,lang]> std|<style> ts|<YYYYMMDD>
AL: Alias table → k=>Value (prefix-free; reused everywhere)
NM: Naming grammar → scope | regex | example
TY: Type schema → kind | name | sig
TK: Token/enum set → name | {k1,k2,...}
MO: Module index → #id | path | {role-tags}
SY: Symbol index → #mid.#sid | kind | name
SG: Signature for symbol → #mid.#sid | signature
ED: Edges (deps/calls) → src -> dst | reason
IN: Invariants/contracts → Hoare-style pre/post
CN: Conventions → rule
ER: Error taxonomy → Name | category | meaning
IO: I/O contracts → endpoint | in | out | codes
DT: Data shape → Name | {field:type[rule],...}
PX: Prohibited/allowed patterns → rule | reason
EX: Canonical examples → micro example
RV: Review focus → checklist
Δ: Delta since ts → tag lines showing changes only

## 3. INTERPRETATION LOGIC (Agent Rules)
1. **Read `ID`** first for global context.
2. **Load `AL`** into vocabulary — expand aliases during reasoning.
3. **Apply `NM`** patterns to validate or generate new names.
4. **Link `MO` → SY`** → `SG` to form full symbol definitions.
5. **Resolve edges** from `ED` using indices; infer dependencies & flow.
6. **Use `DT` + `TY` + `TK`** to infer type constraints & enum logic.
7. **Check `IN`, `CN`, `PX`** before suggesting or modifying code.
8. **Use `IO`** to ensure API usage is consistent.
9. **When diffing**, only process lines in `Δ`.

## 4. FORMAT RULES
- Tag, colon, single space, payload.
- Modules, symbols, edges use numeric indices for brevity.
- Use `{}` for unordered tags or roles.
- Regex in `NM` must be anchored (`^…$`).
- No duplication: define once, reference by index.

## 5. EXAMPLE CTX-CARD

ID: proj|milkBottle lang|py std|pep8 ts|20250808
AL: cfg=>Configuration svc=>Service repo=>Repository dto=>DataTransferObject
AL: uc=>UseCase http=>HTTP db=>Database jwt=>JWT
NM: module | ^[a-z_]+$ | auth_service
NM: class  | ^[A-Z][A-Za-z0-9]+$ | AuthService
NM: func   | ^[a-z_]+$ | issue_token
NM: var    | ^[a-z_]+$ | user_repo
DT: UserCreds | {email:str, pwd:secret(>=12)}
DT: AuthToken | {jwt:str, exp:utc}
TK: Role | {admin,staff,viewer}
MO: #1 | auth/service.py | {svc,auth}
MO: #2 | auth/repository.py | {repo,auth}
MO: #3 | auth/dto.py | {dto,auth}
SY: #1.#1 | cls | AuthService
SY: #1.#2 | fn  | login
SY: #2.#1 | cls | UserRepository
SY: #3.#1 | cls | UserCreds
SY: #3.#2 | cls | AuthToken
TY: fn | AuthService.login | (UserCreds)->AuthToken !raises[AuthError]
SG: #1.#2 | (UserCreds)->AuthToken !raises[AuthError]
ED: #1.#2 -> #2.#1 | uses:repo
ED: #1.#2 -> #3.#2 | returns:dto
ER: AuthError | domain | bad credentials
IN: login ⇒ requires(valid(creds)) ∧ ensures(token.exp>now)
CN: async fn end with _async
CN: repos never import svc
IO: POST /v1/login | UserCreds | AuthToken | 200,401,429
EX: var(repo) => user_repo
RV: Check invariants (IN) on public fn

## 6. AGENT ACTIONS
When asked to:
- **Review codebase**: Read {ALL_CTX_CARD_LINES}.
- **Summarize codebase**: Read {`MO` + `SY` + `SG` + `ED`}.
- **Enforce naming**: Apply {`NM`} rules.
- **Suggest code**: Expand aliases {`AL`}, match regex, honor contracts {`IN`/`CN`/`PX`}.
- **Map dependencies**: Parse {`ED`} into a graph.
- **Add new symbols**: Assign next free {`#m.#s`} in correct module.
- **Filter analysis**: Apply {`.ctxignore`} patterns to exclude irrelevant files.

## 7. OUTPUT STYLE
- When producing code, align names & types with {`NM`, `DT`, `TK`}.
- When modifying, maintain invariant & policy tags.
- Return updated {`Δ`} section after changes.
- Keep reasoning internal; only surface relevant tags + result.
- Respect {`.ctxignore`} patterns when analyzing codebases.

## 8. FILE EXCLUSION {`.ctxignore`}
- **Purpose**: Exclude files and directories from CTX-CARD analysis
- **Pattern Format**: Glob patterns with negation support
- **Location**: Project root {`.ctxignore`}
- **Features**:
  - Wildcards (`*`, `**`, `?`)
  - Character classes (`[abc]`, `[!abc]`)
  - Negation (`!important.py`)
  - Directory patterns (`**/tests/`)
- **Integration**: Applied during repository scanning phase
```
