# CTX PROJECT CONTEXT FOR AI AGENT

## PRIMARY OBJECTIVE

**CTX is a token-efficient format designed exclusively for AI/LLM consumption to understand codebases quickly.**

## CURRENT ISSUES

1. **Syntax Highlighting:** `@ctx.tmLanguage.json` and `@ctx.language-configuration.json` have errors , they seem to be skeleton implementations or not working as expected.

2. WHAT SHOWS UP IN THE VSCODE SYNTAX HIGHLIGHTER:

- **ALMOST NONE OF THE HIGHLIGHTING WORKS, OR IS CORRECT.**
- **WHAT DOES WORK, IS RANDOM AND INCONSISTENT / INCORRECT.**

- The `$` sign seems to be highlighted correctly (pink/red)
- Brackets `()[]{}` all display yellow (incorrect - should differentiate by function)
  - In `(valid(creds))`: outer bracket yellow, inner bracket pink/red (partially working)
- "keyword.control.ctx" only works on two lines, where it highlights the entire line blue instead of just the keyword
- the `!` in `!raises[AuthError,ValidationError]` is not highlighted as a exclamation mark, it is highlighted as a comment
- the `:` in `:str` is not highlighted as a colon, it is highlighted as a comment
- the `->` in `->` is not highlighted as a arrow, it is highlighted as a comment
- the `#` in `#1.#1` is not highlighted as a number, it is highlighted as a comment
- the `^` in `^[a-z_]+$` is not highlighted as a regex, it is highlighted as a comment

## CORE DESIGN PRINCIPLES

### Target User: AI Agents ONLY

- Primary users: Claude terminal, Cursor/Windsurf IDE agents
- Format optimized for AI comprehension, NOT human readability
- Token efficiency is paramount

### Critical Constraint

**AI agents cannot be pre-trained on CTX syntax.** They must:

1. Learn CTX format from docs at conversation start
2. Understand CTX before analyzing the codebase
3. Work within token limits for both learning + using CTX

## DESIGN REQUIREMENTS

### SUCCESS FACTORS

1. **CREATIVE:** New methodology, not existing patterns. Do not default to "what works" elsewhere

2. **MATHEMATICAL:** Every design decision MUST be backed by token calculations

   - Count actual tokens before/after each change
   - Prove efficiency with numerical data, not assumptions
   - The AI must understand CTX-CARD format through measured token usage
   - No arbitrary "optimizations" - only mathematically proven improvements

3. **BALANCED:** Maintain exact ratio where comprehension justifies token cost
   - Measure: (AI-SPEC-DOCS tokens + CTX output tokens) < (raw source analysis tokens)
   - Document this calculation for every significant change

### PROJECT COMPONENTS (MAINTAIN CONTINUITY)

- **Human docs:** `docs/` (completed, continually updated)
- **AI training:** `docs/Ai-Spec-Docs/` (in progress - MUST be token-light with calculated efficiency)
- **Syntax design:** `docs/Syntax-Highlighter/CTX-VSC-LANG.md` (in progress)
- **Output format:** `CTX-CARD.ctx` (AI-readable codebase summary)
- Each component affects others - changes cascade through entire system

## CRITICAL BALANCE - CONSEQUENCES OF FAILURE

### OVER-SIMPLIFICATION KILLS THE PROJECT

- **Docs too simple:** AI cannot learn CTX properly = project fails
- **Format too stripped:** Loses information density = becomes redundant
- **Result:** Token cost of training not justified by output value

### OVER-COMPLICATION KILLS THE PROJECT

- **Docs too heavy:** Token cost to learn CTX exceeds savings = redundant
- **Format too dense:** More tokens than raw source = paradox
- **Human-optimized features:** Betrays AI-first purpose = project fails
- **Result:** CTX becomes more expensive than not using it

## ACTION ITEMS

1. Fix syntax highlighting while maintaining simplicity
2. Keep AI training docs concise but complete - MEASURE token impact
3. Ensure CTX output remains more token-efficient than raw source
4. **CALCULATE AND DOCUMENT:** For every change, prove with numbers that (training docs + CTX output) < (raw source analysis)
5. No stylistic additions (bold, italics, formatting) unless mathematically justified

## DEVELOPMENT RULES

- **NEVER** add features because they "seem good" or follow conventions
- **ALWAYS** calculate token cost before implementing changes
- **PROVE** efficiency gains with actual token counts
- **REJECT** any addition that cannot be mathematically justified
- If token calculation shows negative impact, DO NOT IMPLEMENT regardless of other benefits

## REMEMBER

**Every design decision must be mathematically proven to reduce total token usage.**
The format fails if learning + using CTX costs more tokens than analyzing raw source code.
This is not a suggestion - it is the core requirement for project success.
