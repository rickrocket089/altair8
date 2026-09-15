# Path D — The Interrogable Narrative

**Origin:** founder, 2026-09-15, in conversation. Written up by Sophie at his
request. The idea is his; the articulation, the evidence check and the kill
criteria are mine.

**Status: parked, not rejected.** On the same day he raised it, the founder
chose to proceed on the conventional assumption — *the sender builds in advance
what they want to communicate* — and to revisit this later. The conditions
under which it returns are at the end of this document. It is written up now,
in full, because a path recorded only in a conversation is a path that quietly
disappears.

---

## 1. The problem statement

Business communication today has a sender and a receiver. That asymmetry is why
we *present* at all.

And the sender, knowing the receiver will have questions the artifact cannot
answer, builds an appendix. Backup slides are **materialised anticipation of
questions** — the sender computes in advance what might be asked, because the
medium can answer nothing at the moment it is asked.

Every consulting deck carries an appendix larger than its body. That is not a
stylistic habit. It is a medium compensating for its own inability to respond.

## 2. What the path is

A communication artifact in which an agent stays resident rather than leaving
when authoring ends. The reader does not receive a finished argument and then
go looking for its support — they move through the narrative and change
resolution at will: zoom in on a claim to reach the evidence beneath it, zoom
out to see where it sits in the whole, ask why something is asserted and get an
answer from the material, in real time.

The appendix stops being a pile behind the deck and becomes the depth of the
document itself.

## 3. What it changes

| | Today | This path |
|---|---|---|
| Structure | linear, author-sequenced | reader-navigated by depth |
| Questions | anticipated, pre-answered in an appendix | answered at the moment they are asked |
| The agent | helps the sender author, then leaves | stays in the communication |
| Failure mode | "that's in the backup, let me find it" | the reader never has to ask for it |

Collaboration tools (Miro and its class) already serve the *symmetric* case —
people structuring thought together. This path addresses the asymmetric case,
which is where presentation actually lives and where nothing has changed.

## 4. Evidence from our own record

**Supporting:**

- **Genially fails on exactly this axis.** Kenji, Sprint 3: navigation topology
  is 100% author-scripted at creation time, with no meaningful runtime
  conditional logic. The closest existing analogue to a non-linear
  communication container cannot do the one thing this path is about. That is a
  documented demarcation, not an assertion.
- **Naledi's Sprint 9 meta-finding**, across data journalism, motion graphics,
  spatial/AR, game UI and scientific visualization: the significant innovations
  are new *relationships between reader and artifact* — pacing control,
  disclosure triggers, positioning — not new chart shapes. Ingrid scoped the
  generalisation down (only 4-5 of 11 patterns support it) but did not overturn
  it. This path is the far end of that axis: the reader does not merely pace,
  they interrogate.
- **Hypothesis 3 is unexamined.** Control exercised through natural-language
  feedback rather than direct manipulation has been in the hypothesis set since
  August with, as Ingrid noted on 2026-09-15, *zero* supporting evidence in the
  record. Eleven sprints on generation, none on control modality. This path
  lives on that unexplored axis.
- **Design principle 4 already names zoom** as part of the ambition. It has
  been read as a visual capability for two months. Nobody has read it as a
  *communication mechanism*.

**Against, or unresolved:**

- **Sprint 8's confabulation finding.** The pipeline produced structurally
  perfect, substantively invented content. An artifact that answers live can
  invent live, in front of a client.
- **Unstated Bet B** (Ingrid, 2026-09-15): form partly performs credibility and
  intent. A sender may not *want* the receiver to zoom into the assumptions.
  Persuasion and transparency are in tension here.

## 5. What it resolves that the programme had left unstated

Ingrid's Unstated Bet A — that the single artifact is the right unit of
business communication — is resolved by this path in the negative, deliberately
rather than by drift. That is the first time one of the three unstated bets has
been decided in the open.

## 6. Kill criteria

Stated as conditions, so the path can actually fail rather than being argued
about indefinitely.

1. **Liability.** A deck is a commitment; a resident agent answers *in the
   sender's name to things the sender never saw*. If senders will not accept
   that exposure — and business communication is a domain where reputation is
   the product — the path dies here regardless of how good the interaction is.
   This is the first thing to test, not the last, and it is a question for
   people, not for the team.
2. **Grounding.** If answers generated at read time cannot be held to the
   source material at a rate senders find acceptable, the path is unsafe. Note
   that backup slides are not just anticipated, they are *vetted*. Any
   replacement has to match that, not merely approximate it.
3. **Asymmetry is sometimes the point.** If the segments that pay are the ones
   where interrogability is a threat rather than a feature, the path may be
   right and unsellable. Internal decision memos, technical audiences and
   documents meant to be scrutinised are where it should be tested; the pitch
   deck is where it should not.
4. **Latency.** Real-time depth change requires either precomputation or
   generation fast enough not to break the reading. This is the only one of the
   four that is pure engineering, and therefore the least dangerous.

## 7. Dependencies

- **Backlog #23, reframed.** The question is no longer only "does the model
  choose the right form" but **"does it choose the right depth on demand"** —
  which question deserves which resolution. For this path that is the more
  important half, and it is not currently how #23 is written.
- **C1 changes role rather than dying.** A resident agent must be able to state
  what it is committing to and how confident it is. The Commitment Audit stops
  being an artifact format and becomes the governance layer of a live medium —
  a more serious justification than the one C1 has carried so far. Note the
  open prior-art risk: the uncertainty-visualization literature in IEEE TVCG
  (*In Pursuit of Error*, 2018; *Implicit Error, Uncertainty and Confidence in
  Visualization*, 2021), unreached until 2026-09-15.

## 8. The smallest thing that could be in front of a real person

Required of every path before it counts as a product bet rather than an essay.

**Take one real document** — a sprint report, a decision memo, something with an
actual argument and actual supporting material. Render it so that a reader can
move through the narrative and open any claim to the layer beneath it: the
evidence, the caveat, the number's source.

**Precompute every answer. Vet them. Nothing generated at read time.**

That single constraint separates the two questions this path bundles together:

- *Is interrogable depth valuable to readers?* — testable now, with five
  people, in two to three weeks.
- *Can an agent be trusted to answer live?* — the hard one, and not required to
  answer the first.

This is also the point where the founder's chosen direction and this parked path
meet. If the sender builds in advance what they want to communicate, then the
sender is already building the backup material — the appendix exists. Making it
*navigable in place* rather than *appended behind* is the precomputed variant of
this path. It removes the liability problem entirely, and it is buildable now.

**The parked idea is therefore not fully parked: its precomputed form is
reachable from the direction the founder has actually chosen.**

## 9. Conditions for return

This path comes back on the table when any of these is true:

- The precomputed variant (§8) is tested with real readers and depth-navigation
  measurably changes how they read.
- Backlog #23 resolves in favour of internalised structure that can be elicited
  — which is what would make live answering something other than a gamble.
- The grounding problem from Sprint 8 is closed to a standard a sender would
  sign their name to.
