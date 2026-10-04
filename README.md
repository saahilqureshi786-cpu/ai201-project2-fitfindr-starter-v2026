# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> The Unit 3 tools and planning loop are now implemented.
>
> **The rest of this file is the submission.**

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr is a thrift-shopping assistant that accepts a clothing request written
in plain language, such as `vintage graphic tee under $30`.

The agent parses the request into a description, optional size, and optional
maximum price. It searches the available thrift listings, chooses the strongest
matching item, and combines that item with pieces from the user's existing
wardrobe to suggest one or two outfits.

Finally, FitFindr creates a short social-style fit card that includes the
selected item, its price, resale platform, and the overall outfit vibe.

If no listing matches the request, the agent stops before outfit generation and
tells the user to change the description, size, or maximum price.

---

## Tool Inventory

### `search_listings`

- **What it does:** Searches clothing listings using description keywords and optional size and maximum-price filters.
- **Inputs:** `description` (`str`), `size` (`str` or `None`), `max_price` (`float` or `None`).
- **Returns:** A list of matching listing dictionaries containing fields such as `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`, with stronger keyword matches first.
- **Empty case:** Returns an empty list `[]` when no listings match.

### `suggest_outfit`

- **What it does:** Suggests one or two outfits combining the selected thrift item with pieces from the user's existing wardrobe.
- **Inputs:** `new_item` (`dict`), `wardrobe` (`dict` containing an `items` list).
- **Returns:** A non-empty string containing one or two outfit suggestions and short explanations of why the pieces work together.
- **Empty case:** If the wardrobe has no items, returns general styling advice instead of failing or returning an empty string.

### `create_fit_card`

- **What it does:** Creates a short social-media-style caption about the selected thrift find and outfit.
- **Inputs:** `outfit` (`str`), `new_item` (`dict`).
- **Returns:** A 2–4 sentence caption that mentions the item, price, platform, and overall outfit vibe.
- **Empty case:** If `outfit` is empty or whitespace, returns a descriptive message instead of raising an exception.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, store a helpful
message in `session["error"]` and immediately stop. Do not call
`suggest_outfit` or `create_fit_card`. Otherwise, choose the first search
result, save it in `session["selected_item"]`, generate an outfit, generate a
fit card, and return the completed session.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** The query is parsed with regular expressions in
`parse_query()`. It looks for a maximum price after phrases such as `under`,
`below`, or `up to`, and looks for a size after the word `size`. Those parts are
removed from the query and the remaining text becomes the search description.

For example:

```text
vintage graphic tee size M under $30
```

becomes approximately:

```python
{
    "description": "vintage graphic tee",
    "size": "M",
    "max_price": 30.0
}
```

**What moves through the session:** The session starts with the original query
and wardrobe. The parsed query is stored in `session["parsed"]`, search results
go into `session["search_results"]`, the first result is stored in
`session["selected_item"]`, the generated outfit goes into
`session["outfit_suggestion"]`, and the final caption goes into
`session["fit_card"]`.

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

The loop also increments an iteration counter and calls:

```python
trace.check_iterations(count)
```

on every iteration so the agent cannot continue indefinitely if a branch fails
to terminate.

---

## Sample Run

### One full query

```text
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Here are two ways to style your new Y2K butterfly baby tee using pieces from your existing wardrobe:

### Outfit 1: 2000s Streetwear Contrast
* **Top:** Y2K Baby Tee — Butterfly Print (worn over or under)
* **Bottoms:** Baggy straight-leg jeans (dark wash)
* **Outerwear:** Black cropped zip hoodie
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag

**Why it works:** This leans into the authentic Y2K aesthetic by playing with proportions. The fitted, feminine butterfly tee is balanced out by the ultra-baggy dark wash jeans and the chunky white sneakers. Tossing the black cropped zip hoodie on top keeps the silhouette sharp and pulls in the black accents from the accessories.

---

### Outfit 2: Casual Soft-Grunge
* **Top:** Y2K Baby Tee — Butterfly Print
* **Bottoms:** Wide-leg khaki trousers
* **Outerwear:** Vintage black denim jacket
* **Shoes:** Black combat boots
* **Accessories:** Brown leather belt, Black crossbody bag

**Why it works:** This outfit mixes your cottagecore/vintage top with edgier, utilitarian pieces. The pink and purple butterfly print pops against the neutral khaki wide-leg trousers,while the vintage black denim jacket and combat boots add a grounded, grunge contrast that keeps the sweetness of the baby tee from feeling too precious.

  Fit card: Found my ultimate Y2K aesthetic with this butterfly baby tee for only $18.00 onDepop. I paired it with baggy jeans and a cropped hoodie for that perfect 2000s streetwear contrast. Honestly obsessed with how easy this piece is to style!

0 model calls this session, 2 served from cache
```

### Empty-search branch

```text
$ python app.py ask 'designer ballgown size XXS under $5'

  I couldn't find a matching item. Try changing the description, size, or maximum price.

0 model calls this session
```

The empty-search result shows that the branch stops before an outfit or fit card
is generated.

### The three tools, tested one at a time

#### `search_listings`

```text
$ python -c "from tools import search_listings; print([(x['title'], x['price']) for x in search_listings('graphic tee', max_price=30)[:2]])"

[('Y2K Baby Tee — Butterfly Print', 18.0), ('Graphic Tee — 2003 Tour Bootleg Style', 24.0)]
```

The no-match behavior was also tested:

```text
$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"

[]
```

#### `suggest_outfit`

```text
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[1], get_example_wardrobe()))"

Here are two ways to style your new Y2K butterfly baby tee using pieces from your existing wardrobe:

### Outfit 1: 2000s Streetwear Contrast
* **Top:** Y2K Baby Tee — Butterfly Print (worn over or under)
* **Bottoms:** Baggy straight-leg jeans (dark wash)
* **Outerwear:** Black cropped zip hoodie
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag

**Why it works:** This leans into the authentic Y2K aesthetic by playing with proportions. The fitted, feminine butterfly tee is balanced out by the ultra-baggy dark wash jeans and the chunky white sneakers. Tossing the black cropped zip hoodie on top keeps the silhouette sharp and pulls in the black accents from the accessories.

---

### Outfit 2: Casual Soft-Grunge
* **Top:** Y2K Baby Tee — Butterfly Print
* **Bottoms:** Wide-leg khaki trousers
* **Outerwear:** Vintage black denim jacket
* **Shoes:** Black combat boots
* **Accessories:** Brown leather belt, Black crossbody bag

**Why it works:** This outfit mixes your cottagecore/vintage top with edgier, utilitarian pieces. The pink and purple butterfly print pops against the neutral khaki wide-leg trousers,while the vintage black denim jacket and combat boots add a grounded, grunge contrast that keeps the sweetness of the baby tee from feeling too precious.
```

An empty wardrobe was also tested. Instead of raising an error or returning an
empty string, the tool returned general styling advice.

#### `create_fit_card`

```text
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"

I found Vintage Levi's 501 Jeans — Medium Wash, but I do not have an outfit suggestion to turn into a fit card yet.
```

This verifies the tool's empty-outfit behavior without causing an exception.

---

## How I Used AI

### Moment 1

- **What I asked for:** I asked my AI coding assistant to help plan the three FitFindr tools after I inspected the real listing and wardrobe fields.
- **What came back:** The assistant proposed separate responsibilities for listing search, wardrobe-based outfit generation, and fit-card generation.
- **What I changed:** I made the contracts more specific before implementing them. I required `search_listings` to return `[]` when nothing matches, enforced maximum-price filtering, used normalized size tokens instead of loose substring matching, made `suggest_outfit` return general advice for an empty wardrobe, and made `create_fit_card` handle an empty outfit without crashing.

### Moment 2

- **What I asked for:** I asked my AI coding assistant to help debug `agent.py` after I received an `IndentationError`.
- **What came back:** We inspected the relevant lines and found that `parse_query()` had accidentally been placed inside `new_session()`.
- **What I changed:** I moved `parse_query()` back to the module level, verified the file with `python -m py_compile agent.py`, and implemented the planning loop using session state, a `step` variable, and `trace.check_iterations(count)`. I then tested both the successful branch and the no-results branch before committing the implementation.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```text

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```text

```

**Empty search**

```text

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**