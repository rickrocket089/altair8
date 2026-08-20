"""C1 — render an audited argument as a navigable map.

Deterministic. No LLM call: layout is computed in Python and the page ships with
it, so the rendering is reproducible and inspectable rather than regenerated
each run. Javascript handles interaction only -- expand/collapse and category
filtering -- never layout or selection.

The decisions encoded here come from Mateo's spec and Priya's rulings on it,
and each is a place where a plausible alternative was rejected for a reason:

  - STEPPED visual weight, three bands, never continuous (Mateo 4.6, endorsed by
    Priya on the merits). With ordinal confidence there is no information in the
    gap between 0.73 and 0.69 for continuous encoding to preserve, and rendering
    it continuously would assert a precision the scores do not have. Priya added
    a guard: this must not be "upgraded" to continuous later unless the
    calibration question is resolved first.

  - NO NUMERIC CONFIDENCE anywhere the reader can see (Priya 4.6). Band labels
    are epistemic words -- well-supported / partially supported / weakly
    supported. Printing "0.72" would reimport false precision through a
    different door.

  - COLLAPSED NODES ARE VISIBLE BUT MINIMAL (Mateo 4.7, endorsed). Hiding them
    would let a reader believe the primary reading path is the whole argument,
    which breaks the concept's transparency premise. Showing them at full weight
    would destroy the path as a scaffold.

  - EXPANDED NODES RENDER AT THEIR OWN BAND (Priya's specific catch on 4.7).
    A weak claim that was visually suppressed while collapsed must not pop to
    full weight on expansion. Band classes are applied at build time and never
    altered by the expand handler.

  - CATEGORY FILTERING SUPPRESSES, IT DOES NOT REMOVE (concept, field 2). The
    map does not redraw; non-matching claims dim in place, so the reader keeps
    the structure while changing what stands out.
"""
from prototype.commitment_audit.schema import Audit
from prototype.commitment_audit.reading_path import bottleneck, load_bearing_weak_claims

# Category encoding carries a colour AND the category word on every node.
# Colour alone would fail for colourblind readers, and the whole concept turns
# on the reader being able to tell an assumption from evidence at a glance.
CATEGORY_STYLE = {
    "evidence":   ("#20795b", "#eaf5ef", "Evidence"),
    "inference":  ("#4a6fa5", "#eaf0f7", "Inference"),
    "assumption": ("#a16a17", "#f7efe2", "Assumption"),
    "assertion":  ("#6d7679", "#eef0ee", "Assertion"),
}

NODE_W, NODE_GAP, ROW_H, PAD = 250, 34, 172, 40


def _depths(audit: Audit) -> dict[str, int]:
    """Longest path from the root, so a claim never sits above its own support."""
    index = audit.by_id()
    depth: dict[str, int] = {}

    def walk(node_id: str, d: int) -> None:
        if depth.get(node_id, -1) >= d:
            return
        depth[node_id] = d
        for dep in index[node_id].depends_on:
            walk(dep, d + 1)

    walk(audit.root().id, 0)
    return depth


def _layout(audit: Audit) -> tuple[dict[str, tuple[int, int]], int, int]:
    depth = _depths(audit)
    rows: dict[int, list[str]] = {}
    for node_id, d in sorted(depth.items(), key=lambda kv: (kv[1], kv[0])):
        rows.setdefault(d, []).append(node_id)

    width = max(len(r) for r in rows.values()) * (NODE_W + NODE_GAP) - NODE_GAP
    pos: dict[str, tuple[int, int]] = {}
    for d, ids in rows.items():
        row_w = len(ids) * (NODE_W + NODE_GAP) - NODE_GAP
        x0 = PAD + (width - row_w) // 2
        for i, node_id in enumerate(ids):
            pos[node_id] = (x0 + i * (NODE_W + NODE_GAP), PAD + d * ROW_H)
    return pos, width + PAD * 2, PAD * 2 + (max(rows) + 1) * ROW_H


def render(audit: Audit, prp: list[str], tau: float, warnings: list[str]) -> str:
    index = audit.by_id()
    pos, canvas_w, canvas_h = _layout(audit)
    prp_set = set(prp)
    load_bearing = set(load_bearing_weak_claims(audit, tau))
    boat = bottleneck(audit, prp)

    edges = []
    for claim in audit.claims:
        for dep in claim.depends_on:
            if dep not in pos or claim.id not in pos:
                continue
            x1, y1 = pos[claim.id]
            x2, y2 = pos[dep]
            on_path = claim.id in prp_set and dep in prp_set
            edges.append(
                f'<path d="M {x1 + NODE_W // 2} {y1 + 92} '
                f'C {x1 + NODE_W // 2} {y1 + 130}, {x2 + NODE_W // 2} {y2 - 38}, '
                f'{x2 + NODE_W // 2} {y2}" '
                f'class="edge{" edge--path" if on_path else ""}"/>'
            )

    nodes = []
    for claim in audit.claims:
        if claim.id not in pos:
            continue
        x, y = pos[claim.id]
        band_key, band_label = claim.band()
        colour, tint, cat_label = CATEGORY_STYLE[claim.category]
        on_path = claim.id in prp_set
        classes = f"node band-{band_key} cat-{claim.category}"
        classes += " node--path" if on_path else " node--collapsed"
        if claim.id in load_bearing:
            classes += " node--loadbearing"
        affordance = "" if on_path else '<button class="expand" aria-label="Expand">+</button>'
        flag = ('<span class="loadbearing-flag">load-bearing</span>'
                if claim.id in load_bearing else "")
        nodes.append(
            f'<div class="{classes}" style="left:{x}px;top:{y}px" '
            f'data-cat="{claim.category}" data-id="{claim.id}">'
            f'<span class="cat" style="color:{colour};background:{tint}">{cat_label}</span>'
            f'{flag}<p class="claim">{claim.text}</p>'
            f'<span class="band">{band_label}</span>{affordance}</div>'
        )

    warn_html = ""
    if warnings:
        items = "".join(f"<li>{w}</li>" for w in warnings)
        warn_html = (
            '<details class="auditlog"><summary>Audit log — '
            f'{len(warnings)} item(s), not shown to the reader</summary>'
            f'<ul>{items}</ul><p class="auditlog-note">These are flags for whoever '
            'reviews the audit, deliberately kept out of the reader-facing map: a '
            'reader cannot interpret them without context, and surfacing them would '
            'be noise competing with the visual encoding.</p></details>'
        )

    boat_txt = (
        f"the whole chain rests on its weakest claim, currently "
        f"<strong>{index[min(prp, key=lambda n: index[n].confidence)].band()[1]}</strong>"
        if prp else "no chain of claims currently clears the threshold"
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>C1 Commitment Audit — {audit.title}</title>
<style>
  :root {{
    --ink:#14181a; --ink-mid:#3c4547; --ink-light:#6d7679;
    --rule:#dadfde; --cream:#ffffff; --cream-dark:#eef0ee; --accent:#20795b;
    --accent2:#a16a17;
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--cream);color:var(--ink);
    font-family:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif;line-height:1.6}}
  header{{padding:2.5rem 2rem 1.4rem;max-width:1100px;margin:0 auto}}
  .kicker{{font-size:.7rem;letter-spacing:.18em;text-transform:uppercase;
    color:var(--accent);font-weight:700}}
  h1{{font-size:1.6rem;font-weight:500;margin:.5rem 0 .8rem;letter-spacing:-.01em}}
  .sub{{color:var(--ink-mid);font-size:.95rem;max-width:70ch;margin:0 0 1rem}}

  .controls{{display:flex;flex-wrap:wrap;gap:1.4rem;align-items:center;
    padding:1rem 1.2rem;background:var(--cream-dark);border-radius:6px;
    max-width:1100px;margin:0 auto 1.6rem;font-size:.85rem}}
  .controls .grp{{display:flex;gap:.45rem;align-items:center;flex-wrap:wrap}}
  .controls .lbl{{font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;
    color:var(--ink-light);font-weight:700}}
  .chip{{border:1px solid var(--rule);background:var(--cream);border-radius:20px;
    padding:.25rem .7rem;cursor:pointer;font:inherit;font-size:.8rem;color:var(--ink-mid)}}
  .chip[aria-pressed="true"]{{background:var(--ink);color:var(--cream);border-color:var(--ink)}}

  .canvas-wrap{{overflow-x:auto;padding:0 2rem 1rem}}
  .canvas{{position:relative;margin:0 auto;width:{canvas_w}px;height:{canvas_h}px}}
  svg.edges{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}}
  .edge{{fill:none;stroke:var(--rule);stroke-width:1.5}}
  .edge--path{{stroke:var(--accent);stroke-width:2.5}}

  .node{{position:absolute;width:{NODE_W}px;background:var(--cream);
    border:1px solid var(--rule);border-radius:5px;padding:.7rem .8rem .6rem;
    transition:opacity .18s, transform .18s}}
  .node .cat{{font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;
    font-weight:700;padding:.12em .5em;border-radius:3px}}
  .node .claim{{margin:.5rem 0 .45rem;font-size:.83rem;color:var(--ink-mid)}}
  .node .band{{font-size:.66rem;letter-spacing:.06em;text-transform:uppercase;
    color:var(--ink-light)}}
  .node .expand{{position:absolute;right:.5rem;bottom:.45rem;width:1.35rem;
    height:1.35rem;border-radius:50%;border:1px solid var(--rule);
    background:var(--cream);color:var(--ink-light);cursor:pointer;font:inherit;
    line-height:1;padding:0}}
  .node .expand:hover{{border-color:var(--accent);color:var(--accent)}}

  /* Stepped bands. Applied at build time; the expand handler never touches
     them, so a weak claim cannot pop to full weight when revealed. */
  .band-high{{transform:scale(1)}}
  .band-medium{{transform:scale(.94);opacity:.86}}
  .band-low{{transform:scale(.88);opacity:.66}}

  .node--path{{border-left:3px solid var(--accent);box-shadow:0 1px 3px rgba(0,0,0,.06)}}
  .node--collapsed{{border-style:dashed}}
  .node--collapsed .claim{{display:none}}
  .node--collapsed.is-open .claim{{display:block}}
  .node--loadbearing{{border-color:var(--accent2)}}
  .loadbearing-flag{{font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;
    color:var(--accent2);font-weight:700;margin-left:.4rem}}
  .node.dimmed{{opacity:.15}}

  footer{{max-width:1100px;margin:0 auto;padding:1rem 2rem 4rem;
    font-size:.85rem;color:var(--ink-light)}}
  .auditlog{{max-width:1100px;margin:0 auto 1.5rem;padding:0 2rem}}
  .auditlog summary{{cursor:pointer;font-size:.8rem;color:var(--accent2);font-weight:600}}
  .auditlog ul{{font-size:.82rem;color:var(--ink-mid);margin:.6rem 0}}
  .auditlog-note{{font-size:.8rem;color:var(--ink-light);max-width:70ch}}
  .legend{{display:flex;gap:1.2rem;flex-wrap:wrap;font-size:.78rem;
    color:var(--ink-light);max-width:1100px;margin:0 auto 1.2rem;padding:0 2rem}}
</style></head><body>

<header>
  <span class="kicker">C1 · Commitment Audit · Sprint 11 prototype</span>
  <h1>{audit.title}</h1>
  <p class="sub">The claims below are the agent's own account of what it is
  asserting and how strongly. Visual weight encodes the agent's confidence, not
  emphasis — a claim it is unsure of looks weaker whether or not the argument
  needs it. The solid green chain is the primary reading path: the shortest route
  from the conclusion down to something grounded, using only claims above the
  current threshold. Everything else is still here, collapsed.</p>
  <p class="sub">Right now, {boat_txt}.</p>
</header>

<div class="controls">
  <div class="grp"><span class="lbl">Show only</span>
    <button class="chip" data-filter="all" aria-pressed="true">All claims</button>
    <button class="chip" data-filter="evidence" aria-pressed="false">Evidence</button>
    <button class="chip" data-filter="inference" aria-pressed="false">Inference</button>
    <button class="chip" data-filter="assumption" aria-pressed="false">Assumption</button>
    <button class="chip" data-filter="assertion" aria-pressed="false">Assertion</button>
  </div>
  <div class="grp"><span class="lbl">Threshold</span>
    <button class="chip" id="expand-all">Expand everything</button>
  </div>
</div>

<div class="legend">
  <span>Solid border, green rule — on the primary reading path</span>
  <span>Dashed border — present but collapsed; click + to open</span>
  <span>Ochre border — the only thing holding up the claim above it</span>
</div>

<div class="canvas-wrap"><div class="canvas">
  <svg class="edges">{''.join(edges)}</svg>
  {''.join(nodes)}
</div></div>

{warn_html}

<footer>
  <p>Prototype, Sprint 11. The audit shown is hand-authored, not agent-generated
  — this tests the rendering and interaction model, not whether a model can
  produce an honest audit of its own claims. That is a separate and, on this
  team's own assessment, more important open question.</p>
  <p>Filtering suppresses rather than removes: the structure stays put so you can
  see what you are choosing not to look at.</p>
</footer>

<script>
  document.querySelectorAll('.expand').forEach(function (b) {{
    b.addEventListener('click', function (e) {{
      e.stopPropagation();
      var n = b.closest('.node');
      var open = n.classList.toggle('is-open');
      b.textContent = open ? '\\u2212' : '+';
      /* band-* classes are never touched here: an expanded weak claim keeps
         its weak rendering, per the designer's explicit instruction. */
    }});
  }});

  document.getElementById('expand-all').addEventListener('click', function () {{
    document.querySelectorAll('.node--collapsed').forEach(function (n) {{
      n.classList.add('is-open');
      var b = n.querySelector('.expand');
      if (b) b.textContent = '\\u2212';
    }});
  }});

  document.querySelectorAll('.chip[data-filter]').forEach(function (chip) {{
    chip.addEventListener('click', function () {{
      var f = chip.dataset.filter;
      document.querySelectorAll('.chip[data-filter]').forEach(function (c) {{
        c.setAttribute('aria-pressed', String(c === chip));
      }});
      document.querySelectorAll('.node').forEach(function (n) {{
        n.classList.toggle('dimmed', f !== 'all' && n.dataset.cat !== f);
      }});
    }});
  }});
</script>
</body></html>"""
