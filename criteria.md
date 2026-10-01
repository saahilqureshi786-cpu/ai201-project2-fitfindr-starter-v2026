# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
`search_listings` uses text and attribute matching over real listing data, so
some phrasings may not match perfectly even when a relevant item exists. I chose
4 of 5 because the full three-tool path should succeed most of the time without
assuming the search step will be perfect on every wording.
---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path should be deterministic because an empty result from
`search_listings` is something the planning loop can check directly. If the
search returns `[]`, the agent should stop before `suggest_outfit` every time
and tell the user what they could change in the query.

---

## 3. The selected item is preserved through session state

For 5 of 5 matching queries, the item stored in
`session["selected_item"]` is the same listing that is passed into
`suggest_outfit`.

**Why this target:**
Passing the selected item through session state is deterministic and does not
depend on model-generated output. Once the agent stores a selected listing in
`session["selected_item"]`, the next tool should receive that exact same listing
every time. A mismatch would mean the agent's state flow is broken.
---

## 4. The fit card includes the key listing details

For at least 4 of 5 matching queries, the final fit card mentions the selected
item, its price, and its platform.

**Why this target:**
`create_fit_card` uses a model, so the exact wording can vary from run to run.
Instead of requiring identical wording, I am checking for three details that
should consistently appear in a useful post: the item, price, and platform.
I chose 4 of 5 because model-generated phrasing can vary, but these details
should be present most of the time.
---

## 5. Search respects the maximum price

For 5 of 5 queries that include a maximum price, every listing returned by
`search_listings` has a price less than or equal to that maximum.

**Why this target:**
Price filtering is deterministic and does not depend on model-generated text,
so I expect it to work every time. A listing above the user's stated budget
would mean the search tool is not respecting one of its required inputs.
---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
