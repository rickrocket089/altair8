# Sprint 11 — C1 Commitment Audit: browser render verification

**Date:** 2026-09-15
**Verified by:** Sophie Marchetti (team leader), on the founder's instruction
**Artifact:** `workspace/outputs/prototype-runs/sprint11-c1-commitment-audit.html`
**Method:** headless Chrome (`chrome.exe --headless=new --screenshot`, window 1400px)
against the real file, three states captured. Not an accessibility or
cross-browser audit — a first-pass "does it actually render as designed" check,
the one Sprints 8, 9 and 11 all shipped without.

This closes a gap that has now recurred three sprints in a row: `run.py` itself
prints *"NOT verified in a real browser — same limitation flagged in Sprints 8
and 9; needs a founder pass."* That line was accurate until today.

## States captured

| File | State |
|---|---|
| `sprint11-c1-default-collapsed.png` | default, τ=0.5, as a reader first sees it |
| `sprint11-c1-expanded.png` | after "Expand everything" |
| `sprint11-c1-tau080-nopath.png` | τ=0.8 re-run — the spec'd "no path above threshold" failure mode |

The τ=0.8 variant was produced by re-running
`python -m prototype.commitment_audit.run --tau 0.8`, written to
`sprint11-c1-tau08-check.html`. It is a verification artifact, not a second
prototype.

## Verdict

**The prototype renders and the core idea is legible.** In the expanded state it
does the thing it was built to do: confidence-derived visual weight is visible,
the green reading path is followable, the load-bearing claim is distinguishable
by its ochre border, and the audit log stays out of the reader's way. The
rendering model is sound. What follows are defects in it, not a verdict against
it.

## Defects found

### 1. Edges detach from their nodes (structural, all states)

`renderer.py:101` starts every edge at a hard-coded `y1 + 92`, and
`renderer.py:50` spaces rows on a fixed `ROW_H = 172`. Neither measures the node
it draws from. Real node heights range from roughly 46px (collapsed) to over
150px (expanded, three-line claim).

Consequences, both visible in the screenshots:
- from a **collapsed** node the edge begins in empty space well below the node's
  bottom border — the connector floats, unanchored;
- from an **expanded** node the edge begins *inside* the node box and emerges
  from its middle.

This is the same class as the Sprint 8 container-autosize bug: a hard-coded
geometric constant standing in for a measurement that only a browser can make.

### 2. The band label is clipped by the expand button (default state)

In the collapsed state the category chip and the band label sit on one line and
run into the `+` button: "PARTIALLY SUPPORTEI" on `cost_neutral` and `timing`.
The band is the *only* confidence information a collapsed node carries — and it
is the part that gets cut.

### 3. "LOAD-BEARINGWEAKLY SUPPORTED" runs together

The `.loadbearing-flag` span and the `.band` span have no separator when the
claim text between them is hidden. On the single most important node in the map
— the one the whole argument rests on — the two labels collide into one word.

### 4. Confidence encoding is weakest in the state readers see first

C1's premise is that visual weight derives from confidence. In the collapsed
default state, node height is dominated by whether the claim text is hidden, not
by the band: all collapsed nodes look near-identical regardless of confidence,
and the `band-low` `scale(.88)` difference is barely perceptible on a 46px box.
The encoding that is the entire point of the concept is legible mainly *after*
the reader expands everything.

This is a design finding, not a bug — but it is the one worth arguing about.

### 5. "THRESHOLD" labels a control group that contains no threshold control

The controls bar reads `THRESHOLD | Expand everything`. τ is real and
implemented (`reading_path.py`), but it is baked in at build time by
`run.py --tau`, and the reader can neither see its value nor change it. The
header prose meanwhile tells the reader the path uses "only claims above the
current threshold" — naming a parameter the interface never exposes.

### 6. The spec'd no-path failure mode is softened, not implemented as specified

Mateo's scaffold spec (§ "Case 1: No claim above threshold") requires: do not
render a PRP, display the root node alone marked below-threshold, and show a
**banner** — explicitly *"Do not silently render the full map as if the PRP
succeeded — that hides the failure."*

What τ=0.8 actually produces: the full map renders as normal, with no reading
path and one sentence changed in the intro paragraph — *"Right now, no chain of
claims currently clears the threshold."* Not silent, so the spec's worst case is
avoided; but a prose sentence in a paragraph above a normal-looking map is not
the banner the spec called for, and the root is not marked. A reader who does
not read the intro sees a map that looks fine.

The same holds for the second spec'd case (a load-bearing claim below threshold
required for any path): at τ=0.8 two such claims exist, and both are flagged
ochre in the map, but the loud explicit surfacing the spec called a "load-bearing
confession" is not there.

## What this does not cover

Hand-authored audit content, so nothing here says anything about whether an
agent can produce an honest audit of its own claims — open backlog item #24, and
on this team's own assessment the more important question. One browser, one
viewport width, no interaction beyond "Expand everything", no accessibility pass.

---

# Second pass — after Ingrid's close review (2026-09-15)

Ingrid blocked the Sprint 11 close on three of the six defects above (Blocks A,
B and C) and required a second render verification before resubmission. This is
that pass. Screenshots: `sprint11-c1-pass2-*.png`.

## Block A — band label clipped by the expand button: **fixed**

`.node--collapsed` now reserves right padding for the button and puts the band
on its own line. "PARTIALLY SUPPORTED" reads in full on every collapsed node.

## Block B — "LOAD-BEARINGWEAKLY SUPPORTED": **fixed**

The load-bearing flag is a block element in the collapsed state. The node now
reads, on three lines: ASSUMPTION / LOAD-BEARING / WEAKLY SUPPORTED.

## Block C — the spec'd no-path failure mode: **implemented**

At τ=0.8 the render now shows the conclusion alone, marked "no reading path
clears the threshold", under an ochre banner that states the threshold, says
plainly that nine further claims exist and are being held back, and names the
two below-threshold claims any path would have to cross, each with its band.
That last part is the spec's Case 3 "load-bearing confession", which previously
existed only as an ochre border with nothing telling the reader to look for it.

Three follow-on inconsistencies surfaced while building the failure state and
were fixed in the same pass, because a prototype about honest self-account
cannot leave standing text that contradicts its own banner:

- the intro paragraph still promised "Everything else is still here, collapsed"
  while the banner said the opposite — now conditional on the state;
- the legend still described a green reading path and dashed collapsed nodes,
  neither of which the failure state draws — now replaced by the one line that
  applies;
- the root's marker read "NO READING PATH CLEARS T" because `τ` under
  `text-transform:uppercase` renders as a capital tau, indistinguishable from a
  Latin T. Written out in words instead.

## Not fixed, carried as backlog per Ingrid's ruling

Defect 1 (edges start at a hard-coded `y1 + 92` instead of measuring the node,
so they detach from collapsed nodes and emerge from inside expanded ones),
Defect 4 (confidence encoding weakest in the default collapsed state — a design
decision, not a bug), Defect 5 ("THRESHOLD" labels a group with no threshold
control).

One further wart noticed in this pass and not fixed: in the failure state the
category filters and "Expand everything" remain in the controls bar although
only one node is drawn. Minor, and it belongs with Defect 5 — the controls bar
needs one pass of its own.

## Method note

Headless Chrome again, same three states, plus an expanded-state capture driven
by an injected `load` handler that clicks "Expand everything" (the prototype
file itself is unmodified; the click is injected into a scratch copy). Still one
browser, one viewport, no accessibility pass.
