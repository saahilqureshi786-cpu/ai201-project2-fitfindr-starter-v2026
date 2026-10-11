# FitFindr

FitFindr is an AI thrift-shopping assistant that searches secondhand clothing
listings, selects a relevant item, combines it with pieces from a user's
wardrobe, and generates a short social-style fit card.

> **Setup and commands:** See [RUNNING.md](RUNNING.md).

---

# Unit 3 — Build

## What This Does

A user can ask FitFindr for something in plain language, for example:

```text
vintage graphic tee under $30
```

FitFindr:

1. Parses the request into a description, optional size, and optional maximum
   price.
2. Searches thrift listings.
3. Selects the strongest matching result.
4. Suggests one or two outfits using the selected item and the user's wardrobe.
5. Creates a short fit-card caption.

If the search cannot find anything, the agent stops before outfit generation
and returns an actionable message instead of sending bad data into the model.

During Unit 4, the search behavior was extended so that a failed
size-constrained search retries once without the size filter and explicitly
tells the user what constraint was dropped.

---

## Tool Inventory

### `search_listings`

**Purpose:** Search thrift listings using clothing keywords and optional
constraints.

**Inputs:**

- `description: str`
- `size: str | None`
- `max_price: float | None`

**Returns:**

```python
list[dict]
```

Each dictionary contains listing information such as title, category, size,
price, colors, style tags, brand, and resale platform.

**Empty case:** Returns:

```python
[]
```

when nothing matches.

**Unit 4 MCP status:** This tool is exposed by `mcp_server.py` and called by the
agent through:

```python
mcp_client.call_tool("search_listings", ...)
```

---

### `suggest_outfit`

**Purpose:** Generate one or two outfit suggestions around the selected thrift
item.

**Inputs:**

- `new_item: dict`
- `wardrobe: dict`

**Returns:**

```python
str
```

The string contains outfit suggestions and short explanations.

**Empty case:** If the user has no wardrobe items, the tool returns general
styling advice instead of failing.

This tool remains a local Python tool.

---

### `create_fit_card`

**Purpose:** Generate a short social-media-style caption for the selected item
and outfit.

**Inputs:**

- `outfit: str`
- `new_item: dict`

**Returns:**

```python
str
```

The current prompt requires the exact selected listing title, exact two-decimal
price, and exact platform to appear in the generated caption.

**Empty case:** If the outfit is empty or whitespace, the implementation
returns a descriptive fallback message.

**Unit 4 stretch MCP status:** This became the second FitFindr tool exposed by
`mcp_server.py` and is called through:

```python
mcp_client.call_tool("create_fit_card", ...)
```

---

## Planning Loop

The planning loop lives in:

```text
agent.py::run_agent
```

The query parser lives in:

```text
agent.py::parse_query
```

For example:

```text
90s track jacket size M under $50
```

is parsed approximately as:

```python
{
    "description": "90s track jacket",
    "size": "M",
    "max_price": 50.0,
}
```

The main state flow is:

```text
query
  ↓
parsed
  ↓
search_results
  ↓
selected_item
  ↓
outfit_suggestion
  ↓
fit_card
```

### Current branch rule

The normal path is:

```text
search
  ↓
matches?
  ├── yes → select first result
  │         ↓
  │      suggest_outfit
  │         ↓
  │      create_fit_card
  │         ↓
  │        return
  │
  └── no
       ↓
     was a size supplied?
       ├── yes → retry search once without size
       │          ├── matches → continue normal path
       │          └── empty → stop with helpful error
       │
       └── no → stop with helpful error
```

The agent stores all intermediate values in session state, including:

```python
session["parsed"]
session["search_results"]
session["selected_item"]
session["outfit_suggestion"]
session["fit_card"]
session["error"]
session["notice"]
```

The loop also calls:

```python
trace.check_iterations(count)
```

so an unexpected branch cannot run indefinitely.

---

## Sample Run

Current full-agent trace:

```text
$ python app.py ask 'vintage graphic tee under $30' --trace

[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 3 items: Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey, Y2K Baby Tee — Butterfly Print
      →    matches found; selecting the first result

[2] suggest_outfit
      in:  dict with keys: new_item, wardrobe_items
      out: Here are two outfit options using your 2003 tour graphic tee and items from your wardrobe: ...

[3] create_fit_card (via MCP)
      in:  dict with keys: outfit, new_item
      out: I can't believe I scored this Graphic Tee — 2003 Tour Bootleg Style for only $24.00 on depop! ...

Found: Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

Fit card: I can't believe I scored this Graphic Tee — 2003 Tour Bootleg Style
for only $24.00 on depop! I threw it on with some baggy denim and combat boots
for an effortless grunge streetwear vibe that feels straight out of the early
2000s.
```

### Tool test — `search_listings`

```text
$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"

[]
```

This verifies the empty-search return shape.

### Tool test — `suggest_outfit`

`suggest_outfit` was tested with the example wardrobe and returned non-empty
outfit suggestions using specific wardrobe pieces.

It was also tested with:

```text
python app.py ask 'denim jacket under $50' --empty-wardrobe
```

and returned general styling advice rather than crashing.

### Tool test — `create_fit_card`

The empty-outfit behavior was tested directly:

```text
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"

I found Vintage Levi's 501 Jeans — Medium Wash, but I do not have an outfit
suggestion to turn into a fit card yet.
```

---

## How I Used AI

### Moment 1 — planning the tools

I used an AI coding assistant to help reason about how to split FitFindr into
three separate tools after examining the listing and wardrobe data.

The assistant suggested separate search, styling, and fit-card responsibilities.

I made the contracts more specific by requiring:

- an explicit `[]` empty result from search,
- deterministic maximum-price filtering,
- normalized size handling,
- a useful empty-wardrobe path,
- and a non-crashing empty-outfit path.

### Moment 2 — debugging the planning loop

I used an AI coding assistant while debugging an `IndentationError` in
`agent.py`.

The problem was that `parse_query()` had accidentally been placed inside
`new_session()`.

I corrected the function structure, verified the file with:

```text
python -m py_compile agent.py
```

and then tested both the successful and empty-search branches before committing
the implementation.

---

# Unit 4 — Testing

## Unit 4 Stretch Features — Declared Before Build

Before implementing the stretch work, I declared that I would attempt all three
Unit 4 stretch features:

1. **Second tool moved onto MCP:** After moving `search_listings` onto MCP, I
   would expose another FitFindr tool through MCP and demonstrate a run through
   that path.
2. **Retry with looser constraints:** When a search fails because of a size
   constraint, retry once without size and clearly say what was dropped.
3. **Second measured improvement:** Make a second change based on diagnosis and
   run a third evaluation.

These declarations were committed before the stretch features were built.

---

## Run Log — Before

Raw log:

```text
results/run_2026-10-11_1753_before.md
```

Produced by:

```text
run_eval.py::main
```

Agent loop:

```text
agent.py::run_agent
```

The original five criteria in `criteria.md` were not changed.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | ≥4/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 2. Impossible query stops before second tool | 5/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 3. Selected item preserved through session state | 5/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 4. Fit card includes selected item, price, and platform | ≥4/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 5. Search respects maximum price | 5/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |

### Real output from one baseline try

This output came from:

```text
results/run_2026-10-11_1753_before.md
run_eval.py::main
agent.py::run_agent
```

```text
Query: vintage graphic tee under $30

selected_item:
Y2K Baby Tee — Butterfly Print ($18.0, depop)

search_results: 10

Trace:

[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print,
           Graphic Tee — 2003 Tour Bootleg Style,
           Vintage Band Tee — Faded Grey … +7 more
      →    matches found; selecting the first result

[2] suggest_outfit
      in:  dict with keys: new_item, wardrobe_items

[3] create_fit_card
      in:  dict with keys: outfit, new_item

Fit card:

Found the ultimate Y2K butterfly baby tee while thrifting today and I’m
literally obsessed. Scored it for just $18.00 and just posted it over on Depop
if anyone wants it! Paired it with baggy denim and chunky sneakers for that
effortless, loose-on-the-bottom streetwear vibe.
```

---

## Verdicts and Diagnoses

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | ≥4/5 | MET — 5/5 | Every try searched, generated an outfit, and generated a fit card. |
| 2 | Impossible query stops before second tool | 5/5 | MET — 5/5 | Every impossible-query try stopped after search and never called `suggest_outfit`. |
| 3 | Selected item preserved through session state | 5/5 | MET — 5/5 | The same selected listing was stored in session and used in the downstream outfit step on every try. |
| 4 | Fit card includes selected item, price, and platform | ≥4/5 | MET — 5/5 | All five captions referred to the selected denim jacket, its $42 price, and Poshmark. |
| 5 | Search respects maximum price | 5/5 | MET — 5/5 | Every returned result for the `$25` scenario stayed at or below the requested maximum. |

### Diagnosis

None of the original five criteria missed their Unit 3 targets.

Because there were no misses, I looked for a target that was too easy.

The clearest one was **Criterion 4**. Its original target only required the
fit card to *mention* the item, price, and platform in at least 4 of 5 tries.
The baseline technically passed, but the model regularly paraphrased the item
title and formatted the price inconsistently.

I therefore defined a stricter diagnostic target without changing the original
criterion:

> **Tighter Criterion 4 target:** In 5 of 5 tries, the fit card should contain
> the exact selected listing title, the exact two-decimal price such as
> `$42.00`, and the exact platform.

Against that stricter target, the baseline denim-jacket outputs scored:

```text
0/5
```

The mechanism was in the `create_fit_card` generation prompt. It asked the
model to mention the listing information, but it did not tell the model that
those fields had to be reproduced exactly. The model therefore legitimately
paraphrased them.

I did **not** lower or rewrite the original acceptance criterion.

---

## Failure Modes Triggered on Purpose

### 1. Empty search

Command:

```text
python app.py ask 'designer ballgown size XXS under $5' --trace
```

The search returned no result. After the retry feature was added, the agent also
retried once without `XXS`, still received no results, and stopped before
`suggest_outfit`.

Current behavior:

```text
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    no matches; retrying once without the size filter 'XXS'

[2] search_listings retry (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    dropped size constraint 'XXS'

I couldn't find a matching item. I retried without the size filter
(dropped size XXS) and still found nothing. Try changing the description
or maximum price.
```

This is actionable because it tells the user what was tried and what they can
change.

### 2. Empty wardrobe

Command:

```text
python app.py ask 'denim jacket under $50' --empty-wardrobe
```

The agent did not crash. `suggest_outfit` detected that the wardrobe contained
no saved items and returned general styling guidance instead.

### 3. Model unavailable

The model failure was deliberately triggered using an invalid key and cache
disabled.

The trace reached `suggest_outfit`, caught `ModelUnavailable`, and returned:

```text
The AI model couldn't be reached, so I couldn't create an outfit suggestion.
Check your API key or internet connection, then try again.
```

The failure is handled instead of producing a Python traceback for the user.

---

## Loop Trace

### Happy path

This is a current run after both MCP migrations:

```text
$ python app.py ask 'vintage graphic tee under $30' --trace

[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 3 items: Graphic Tee — 2003 Tour Bootleg Style,
           Vintage Band Tee — Faded Grey,
           Y2K Baby Tee — Butterfly Print
      →    matches found; selecting the first result

[2] suggest_outfit
      in:  dict with keys: new_item, wardrobe_items
      out: Here are two outfit options using your 2003 tour graphic tee ...

[3] create_fit_card (via MCP)
      in:  dict with keys: outfit, new_item
      out: I can't believe I scored this Graphic Tee — 2003 Tour Bootleg Style
           for only $24.00 on depop! ...
```

The trace visibly shows both MCP calls and the local model tool between them.

### Empty path

```text
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    no matches; retrying once without the size filter 'XXS'

[2] search_listings retry (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    dropped size constraint 'XXS'
```

There is no `suggest_outfit` or `create_fit_card` call after the second empty
result.

### On the MCP move

The required MCP migration was `search_listings`.

Instead of importing and calling the function directly, `run_agent()` now uses:

```python
call_tool(
    "search_listings",
    search_inputs,
)
```

`mcp_server.py` registers the tool with typed inputs, while `mcp_client.py`
starts the server, calls the tool, and converts the MCP response back to its
native Python value.

The behavior stayed compatible with the rest of the planning loop: a successful
search still returned `list[dict]`, while a failed search returned `[]`.

---

# Improvement 1 — Stricter Fit-Card Metadata

## What I changed

I rewrote the `create_fit_card` prompt so that it explicitly requires:

- the exact listing title,
- the exact two-decimal price,
- the exact platform,
- and prohibits paraphrasing or reformatting those three fields.

For example, the prompt now supplies:

```text
Exact item title: Denim Jacket — Light Wash, Cropped
Exact price: $42.00
Exact platform: poshmark
```

and instructs the model to reproduce those values exactly.

## Which diagnosis it addressed

This change addressed the stricter version of Criterion 4 identified in the
baseline diagnosis.

The original criterion passed, but the model was free to change:

```text
Denim Jacket — Light Wash, Cropped
```

into wording such as:

```text
cropped light wash denim jacket
```

and to turn:

```text
$42.00
```

into:

```text
$42
```

The issue was therefore in the generation prompt rather than search, session
state, or the planning branch.

---

## Run Log — After Improvement 1

Raw log:

```text
results/run_2026-10-11_1758_after.md
```

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | ≥4/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 2. Impossible query stops before second tool | 5/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 3. Selected item preserved through session state | 5/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 4. Fit card includes selected item, price, and platform | ≥4/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 5. Search respects maximum price | 5/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |

### Stricter Criterion 4 measurement

Using the stricter target:

```text
exact title + exact $42.00 price + exact platform
```

the result changed from:

```text
Before: 0/5
After:  5/5
```

Example after output:

```text
So obsessed with my new Denim Jacket — Light Wash, Cropped that I scored on
poshmark for only $42.00! It gives off the ultimate effortless streetwear vibe
when I style it with baggy bottoms and chunky sneakers.
```

## Did it help?

Yes.

The five original acceptance criteria remained MET, and the stricter metadata
check improved from **0/5 to 5/5**.

That shows the prompt change fixed the specific formatting problem identified
in the diagnosis.

---

# Stretch Feature — Retry With Looser Constraints

The retry stretch was declared before implementation.

When a size-constrained search returns nothing, the agent now retries exactly
once with:

```python
size=None
```

It also tells the user that the size constraint was removed.

Diagnostic query:

```text
90s track jacket size XS
```

Trace:

```text
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    no matches; retrying once without the size filter 'XS'

[2] search_listings retry (via MCP)
      in:  dict with keys: description, size, max_price
      out: 2 items: 90s Track Jacket — Navy/White Stripe,
                    Denim Jacket — Light Wash, Cropped
      →    dropped size constraint 'XS'

[3] suggest_outfit
      in:  dict with keys: new_item, wardrobe_items

[4] create_fit_card
      in:  dict with keys: outfit, new_item
```

The user-facing notice is:

```text
No matches were found in size XS, so I retried without the size filter.
```

---

# Improvement 2 — Item-Type Search Ranking

## Diagnosis

While testing the new retry branch, I found another quality problem.

For:

```text
90s track jacket size XS
```

the first search correctly returned nothing.

The retry correctly removed the `XS` size constraint, but the earlier search
ranking could select a **bucket hat** instead of the requested track jacket.

The problem was in `search_listings`.

The search gave credit to overlapping words such as:

```text
90s
```

without giving enough importance to the requested item type:

```text
jacket
```

That meant an unrelated listing could rank highly after constraints were
loosened.

## What I changed

I changed the search scoring so that clothing-type words such as:

```text
jacket
dress
tee
boots
hat
```

receive stronger weight.

When a query explicitly names an item type, the listing must now match that
item type in an important field such as its title, category, or style metadata.

This was one isolated search-ranking change.

---

## Run Log — Second Improvement

Raw third run:

```text
results/run_2026-10-11_1812_second_improvement.md
```

The original five criteria remain in the same comparison format:

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | ≥4/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 2. Impossible query stops before second tool | 5/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 3. Selected item preserved through session state | 5/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 4. Fit card includes selected item, price, and platform | ≥4/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |
| 5. Search respects maximum price | 5/5 | PASS | PASS | PASS | PASS | PASS | MET — 5/5 |

I also added one diagnostic scenario without changing the five official
criteria:

| Diagnostic scenario | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Result |
|---|---|---|---|---|---|---|---|
| Retry without size selects requested item type | Track jacket selected | PASS | PASS | PASS | PASS | PASS | 5/5 |

Every diagnostic try selected:

```text
90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
```

instead of an unrelated item.

## Did Improvement 2 help?

Yes for the ranking defect that motivated the change.

The original five acceptance-criterion scores stayed at **5/5**, so this
improvement did not change their official verdicts.

However, the problematic fallback search changed from selecting an unrelated
bucket hat in the manual pre-change test to selecting:

```text
90s Track Jacket — Navy/White Stripe
```

in **5/5 diagnostic tries** after the ranking change.

So the improvement fixed the diagnosed ranking behavior while preserving all
five original acceptance-criterion results.

---

# Stretch Feature — Second Tool on MCP

The second MCP tool was also declared before implementation.

The final `mcp_server.py` exposes:

```text
search_listings
create_fit_card
```

Running:

```text
python mcp_client.py
```

shows:

```text
search_listings
    - description: string
    - size: string (optional)
    - max_price: number (optional)

create_fit_card
    - outfit: string
    - new_item: object
```

The agent now calls both tools through MCP.

A final traced run proves the second MCP path is actually used:

```text
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 3 items: Graphic Tee — 2003 Tour Bootleg Style,
           Vintage Band Tee — Faded Grey,
           Y2K Baby Tee — Butterfly Print
      →    matches found; selecting the first result

[2] suggest_outfit
      in:  dict with keys: new_item, wardrobe_items

[3] create_fit_card (via MCP)
      in:  dict with keys: outfit, new_item
      out: I can't believe I scored this Graphic Tee — 2003 Tour Bootleg Style
           for only $24.00 on depop! ...
```

This demonstrates that `create_fit_card` was not only registered on the MCP
server but was also used through the MCP client by the actual planning loop.

---

# What's Still Broken

None of the five original acceptance criteria are currently missed.

There are still limitations outside those five criteria.

### Search is still primarily keyword based

The improved ranking handles explicit item types much better, but it is not a
full semantic fashion-search system. A vague query using synonyms that do not
appear in listing metadata could still rank poorly.

A next improvement would be to combine the deterministic filters with semantic
or hybrid search.

### Query parsing is intentionally simple

`parse_query()` uses regular expressions for prices and explicit `size ...`
phrasing.

More conversational requests could require a more robust structured parser.

### Model-backed tools still depend on model availability

`suggest_outfit` and the implementation behind `create_fit_card` require the
configured model to be available.

The agent now handles model failure with an actionable message, but it cannot
produce model-generated styling content while the model itself is unavailable.

These limitations did not cause any of the original five acceptance criteria
to miss during the measured runs, so I stopped here rather than adding
unmeasured changes after the experiments.

---

# Evaluation Summary

### Baseline

```text
results/run_2026-10-11_1753_before.md
```

Original acceptance criteria:

```text
Criterion 1: 5/5 — MET
Criterion 2: 5/5 — MET
Criterion 3: 5/5 — MET
Criterion 4: 5/5 — MET
Criterion 5: 5/5 — MET
```

Stricter exact-metadata diagnostic:

```text
0/5
```

### After Improvement 1

```text
results/run_2026-10-11_1758_after.md
```

Original criteria remained:

```text
5/5
5/5
5/5
5/5
5/5
```

Stricter exact-metadata diagnostic:

```text
5/5
```

### After Improvement 2

```text
results/run_2026-10-11_1812_second_improvement.md
```

Original criteria remained:

```text
5/5
5/5
5/5
5/5
5/5
```

Retry/item-type diagnostic:

```text
5/5
```

No original criterion was revised or lowered after seeing the results.

---

# Final Unit 4 Feature Summary

Required work completed:

- `search_listings` moved onto MCP
- three failure modes intentionally triggered and handled
- full loop tracing added
- five original criteria tested five times each
- baseline verdicts recorded
- no-miss diagnosis supplied by tightening Criterion 4
- first improvement measured with a complete second run
- before and after results compared
- remaining limitations documented

Declared stretch work completed:

- second MCP tool: `create_fit_card`
- retry once without size and explicitly report dropped constraint
- second measured improvement
- third evaluation run
- diagnostic retry scenario succeeded 5/5

---

# Final Verification

The project was syntax checked throughout development using commands such as:

```text
python -m py_compile agent.py
python -m py_compile tools.py
python -m py_compile scenarios.py
python -m py_compile mcp_server.py
```

The project test suite was also run after the changes:

```text
python test.py
```

Result:

```text
10 passed
```

The same repository from Unit 3 was retained so the Git commit history preserves
the original acceptance criteria and the order of the Unit 4 testing work.

---

## Running the Project

See:

[RUNNING.md](RUNNING.md)