"""Real Draco-based Layer-1 algorithmic ground truth for Sprint 13.

Backlog #23's protocol specified "VizML/Draco/Voyager algorithmic
consensus" for Layer 1. Verified 2026-09-16 that only Draco is actually
reachable -- neither VizML nor Voyager has an installable package or a
callable API. This is a real, disclosed deviation from the pre-registered
three-tool consensus, not something to paper over: Layer 1 ground truth in
this sprint is Draco alone. See the sprint record for the founder's
decision on how to proceed given this gap.

Real, tested Draco usage (not guessed from stale docs): field facts come
from `draco.schema.schema_from_dataframe` + `draco.fact_utils.dict_to_facts`
on a synthetic DataFrame built to match each scenario's extracted field
spec (agents/researcher/backlog23_field_extraction.py); a partial spec adds
placeholder `entity(view/mark/encoding, ...)` facts (with entity IDs
offset well clear of the field IDs draco assigns 0..N -- an id collision
here silently produces infinite recursion in `answer_set_to_dict`, caught
and fixed during real testing) asking Draco to encode each meaningful field;
`Draco().complete_spec()` returns the optimal completion, parsed back to a
dict.

ID-like categorical fields (cardinality == number_rows, i.e. every row is
its own category) are excluded from the fields Draco is asked to encode --
they're identifiers, not something a chart would meaningfully encode.
"""
import random

import pandas as pd
import draco as drc
from draco.schema import schema_from_dataframe
from draco.fact_utils import dict_to_facts, answer_set_to_dict

_ENTITY_ID_OFFSET = 10_000  # clear of any real field id draco assigns


def build_synthetic_dataframe(field_spec: dict, seed: int = 0) -> pd.DataFrame:
    """field_spec: {"number_rows": int, "fields": [{"field_name", "type",
    "approximate_cardinality"}, ...]} -- the structure
    backlog23_field_extraction.py produces. Builds plausible synthetic data
    matching each field's type and (if given) cardinality; values
    themselves don't matter for Draco's schema-level recommendation, only
    type/uniqueness/distribution shape do.
    """
    rng = random.Random(seed)
    n = field_spec["number_rows"]
    data = {}
    for f in field_spec["fields"]:
        name = f["field_name"]
        ftype = f["type"]
        if ftype == "ordinal_or_temporal":
            # A real ordered sequence -- generate it as actual ordered
            # values (0..n-1), not shuffled categories, so draco's schema
            # inference (entropy/uniqueness) reflects genuine order, not
            # nominal noise. High cardinality here is expected and correct.
            data[name] = list(range(n))
        elif ftype == "nominal":
            k = f.get("approximate_cardinality") or max(2, min(n, 5))
            k = max(1, min(k, n))
            categories = [f"{name}_{i}" for i in range(k)]
            data[name] = [rng.choice(categories) for _ in range(n)]
        elif ftype == "boolean":
            data[name] = [rng.choice([True, False]) for _ in range(n)]
        else:  # continuous
            data[name] = [rng.gauss(50, 15) for _ in range(n)]
    return pd.DataFrame(data)


def _meaningful_fields(field_spec: dict) -> list[str]:
    """Exclude pure-identifier NOMINAL fields only (cardinality == rows,
    e.g. batch_id). Never exclude ordinal_or_temporal fields on cardinality
    grounds -- a 60-year ordered sequence has cardinality == rows and is
    normally the single most important field to encode (real bug caught
    2026-09-16: the original cardinality-only heuristic dropped every
    date/year/week axis from every time-series scenario's recommendation)."""
    n = field_spec["number_rows"]
    return [
        f["field_name"] for f in field_spec["fields"]
        if not (f["type"] == "nominal" and (f.get("approximate_cardinality") or 0) == n)
    ]


def get_draco_recommendation(field_spec: dict, seed: int = 0) -> dict:
    """Returns {"mark_type": str, "encodings": [{"field","channel"}, ...],
    "raw_spec": dict, "encoded_fields": [...], "excluded_id_fields": [...]}."""
    df = build_synthetic_dataframe(field_spec, seed=seed)
    schema = schema_from_dataframe(df)
    field_facts = dict_to_facts(schema)

    meaningful = _meaningful_fields(field_spec)
    excluded = [f["field_name"] for f in field_spec["fields"] if f["field_name"] not in meaningful]

    view_id = _ENTITY_ID_OFFSET
    mark_id = _ENTITY_ID_OFFSET + 1
    placeholder_facts = [
        f"entity(view,root,{view_id}).",
        f"entity(mark,{view_id},{mark_id}).",
    ]
    for i, fname in enumerate(meaningful):
        enc_id = _ENTITY_ID_OFFSET + 2 + i
        placeholder_facts.append(f"entity(encoding,{mark_id},{enc_id}).")
        placeholder_facts.append(f"attribute((encoding,field),{enc_id},{fname}).")

    input_spec = field_facts + placeholder_facts

    d = drc.Draco()
    try:
        model = next(d.complete_spec(input_spec, models=1))
    except StopIteration:
        return {
            "mark_type": None, "encodings": [], "raw_spec": None,
            "encoded_fields": meaningful, "excluded_id_fields": excluded,
            "error": "no completion found (unsatisfiable spec)",
        }
    spec = answer_set_to_dict(model.answer_set)

    views = spec.get("view") or []
    if not views or not views[0].get("mark"):
        return {
            "mark_type": None, "encodings": [], "raw_spec": spec,
            "encoded_fields": meaningful, "excluded_id_fields": excluded,
            "error": "completion had no mark",
        }
    mark = views[0]["mark"][0]
    encodings = [
        {"field": e.get("field"), "channel": e.get("channel")}
        for e in mark.get("encoding", [])
    ]
    return {
        "mark_type": mark.get("type"),
        "encodings": encodings,
        "raw_spec": spec,
        "encoded_fields": meaningful,
        "excluded_id_fields": excluded,
        "error": None,
    }
