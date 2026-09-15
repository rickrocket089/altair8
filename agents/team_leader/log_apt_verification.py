from tools import db
db.set_memory("team_leader", "apt_boz_verification", """VERIFICATION ADDENDUM to kenji/c1_uncertainty_literature_check, section 4.
Written by Sophie 2026-09-15. Kenji's own brief is unmodified -- this is a
separate note, because a filed brief should not be edited after the fact by
someone else.

Kenji labelled his entire section 4 as RECOLLECTION, correctly and
self-critically, because his ten designed queries returned nothing for
Mackinlay or Casner. Both papers were retrieved within minutes by literal
title-phrase queries against the same fixed connector. His queries were the
weaker instrument, not the source.

RETRIEVED, both open access, both with free full-text PDFs at dl.acm.org:

1. Mackinlay, "Automating the design of graphical presentations of relational
   information", ACM Transactions on Graphics, 1986.
   https://dl.acm.org/doi/pdf/10.1145/22949.22950
   Abstract: an application-independent presentation tool that automatically
   designs effective graphical presentations of RELATIONAL INFORMATION. Graphic
   design issues are codified as EXPRESSIVENESS criteria (can the graphical
   language express the desired information) and EFFECTIVENESS criteria (is the
   encoding perceptually good). Inputs are the information and the criteria.
   NO AUDIENCE MODEL APPEARS IN THE ABSTRACT.

2. Casner, "Task-analytic approach to the automated design of graphic
   presentations", ACM Transactions on Graphics, 1991.
   https://dl.acm.org/doi/pdf/10.1145/108360.108361
   Abstract: BOZ designs graphics from an analysis of THE TASK the graphic is
   meant to support -- substituting perceptual inferences for logical ones and
   minimising visual search. TASK is the added input.
   AGAIN NO AUDIENCE MODEL IN THE ABSTRACT.

WHAT THIS ESTABLISHES: Kenji's recollection was accurate at abstract level. The
formal tradition ran data type (Mackinlay) and then task (Casner), and did not
take the audience as an input. Hypothesis 2 -- that visual form should derive
from audience and goal rather than content type alone -- is therefore an
extension of that tradition rather than a rediscovery of it, and this is now
citable rather than remembered.

WHAT IT DOES NOT ESTABLISH: whether either paper discusses audience inside the
body and rules it out, and on what grounds. Both full texts are free. Whoever
next touches hypothesis 2 should read them rather than cite these abstracts --
the reasoning for excluding audience matters more to us than the exclusion.

PROCESS NOTE, worth more than the finding: model-designed queries can be
systematically worse than a literal title search for canonical old work, which
is exactly the material a novelty claim most needs. Kenji's brief would have
rested on recollection in its most strategically load-bearing section if nobody
had checked. Retrieval design should include named-target title queries
alongside conceptual ones whenever specific prior art is already suspected.""")
print("stored")
