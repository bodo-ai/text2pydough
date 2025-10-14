import os
import json
import random
from datetime import datetime
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union
import time

import pandas as pd

# External dependencies used by selection/ensemble logic
import gradio_agent_v2
from test_data.eval import symetric_compare_df
from numbers import Number


# === Global RNG (seeded) ===
RNG_SEED = 12345
rng = random.Random(RNG_SEED)


# === Helper for LLM inputs ===
MAX_LLM_ROWS = 100

def to_truncated_records_json(
    gen_df_json: Optional[str], df_obj: Optional[pd.DataFrame], max_rows: int = MAX_LLM_ROWS
) -> str:
    """
    Return a JSON string (records orient) for LLM grading, truncated to at most max_rows.

    Preference order:
    1) Use provided gen_df_json if it is valid JSON; truncate list payloads to max_rows
    2) Otherwise, serialize df_obj with .iloc[:max_rows] to JSON records
    3) On failure, return empty string
    """
    # Try using provided JSON if present
    if isinstance(gen_df_json, str) and len(gen_df_json.strip()) > 0:
        raw = gen_df_json.strip()
        try:
            # Clean common artifacts such as newlines
            cleaned = raw.replace("\n", "").replace("\r", "")
            data = json.loads(cleaned)
            if isinstance(data, list):
                # Truncate list of records
                if len(data) > max_rows:
                    data = data[:max_rows]
                try:
                    return json.dumps(data, ensure_ascii=False)
                except Exception:
                    pass
                # Fall through on dump failure
            elif isinstance(data, dict):
                # Keep dict as-is (rare for records, but safe)
                try:
                    return json.dumps(data, ensure_ascii=False)
                except Exception:
                    pass
            # If other types, fall back to DataFrame path
        except Exception:
            # If parsing fails, fall back to DataFrame path
            pass

    # Fall back: serialize the DataFrame if provided
    if df_obj is not None:
        try:
            truncated = df_obj.iloc[:max_rows]
            return truncated.to_json(orient="records", date_format="iso")
        except Exception:
            return ""

    return ""


def _normalize_value_for_signature(value: Any) -> Any:
    """
    Normalize values for canonical DataFrame signatures so that comparisons
    are robust to minor representation differences. This intentionally keeps
    the representation simple and deterministic.
    """
    try:
        if value is None:
            return None
        # Treat NaN/NaT as None
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass

        # Numbers: round floats to reduce tiny diffs
        if isinstance(value, Number):
            try:
                # Avoid rounding integers unnecessarily
                if float(value).is_integer():
                    return int(value)
                return round(float(value), 6)
            except Exception:
                return float(value)

        # Timestamps / datetimes -> ISO string
        try:
            if hasattr(value, "isoformat"):
                return value.isoformat()
        except Exception:
            pass

        # Strings: trim and lowercase
        if isinstance(value, str):
            s = value.strip().lower()
            # Collapse multiple whitespace
            return " ".join(s.split())

        # Containers: json-stable representation
        if isinstance(value, (list, tuple, dict)):
            try:
                return json.dumps(value, sort_keys=True, ensure_ascii=False)
            except Exception:
                return str(value)

        # Fallback: stable string
        return str(value)
    except Exception:
        return str(value)


def _canonical_df_signature(df_obj: pd.DataFrame, num_rows: int = 10) -> Tuple[Any, ...]:
    """
    Build a canonical signature for a DataFrame that ignores column NAMES and
    column ORDER, based only on the first `num_rows` rows of data.

    Algorithm:
    - Take head(num_rows)
    - For each column, build the vector of normalized values across those rows
    - Sort the set of column vectors lexicographically (ignores original names/order)
    - Transpose into row-wise tuples and return as a tuple including (rows, cols)
    """
    try:
        head_df = df_obj.iloc[: max(0, int(num_rows))]
    except Exception:
        return ("invalid",)

    try:
        # Collect per-column vectors of normalized values
        col_vectors: List[Tuple[Any, ...]] = []
        row_count = len(head_df.index)
        for col in list(head_df.columns):
            try:
                series_vals = [
                    _normalize_value_for_signature(head_df.iloc[r][col]) for r in range(row_count)
                ]
                col_vectors.append(tuple(series_vals))
            except Exception:
                # If any issue, mark the column with a sentinel to keep determinism
                col_vectors.append(("__error__",))

        # Sort columns by their content vectors to remove column-order influence
        col_vectors_sorted = sorted(col_vectors)

        # Transpose back into row tuples
        if col_vectors_sorted:
            row_tuples = list(zip(*col_vectors_sorted))
        else:
            row_tuples = []

        # Include basic shape information to distinguish different structures
        return (row_count, len(col_vectors_sorted), tuple(row_tuples))
    except Exception:
        return ("invalid",)


def selection_random_tie_break(candidate_indices: List[int], question_idx: Union[int, str] = "?") -> Optional[int]:
    """
    Deterministically break ties among candidate indices using a seeded RNG.
    Returns the chosen index from candidate_indices.
    """
    if not candidate_indices:
        return None
    chosen = rng.choice(candidate_indices)
    print(f"[INFO] [Q{question_idx}] Tie-break among {len(candidate_indices)} candidates -> picked index {chosen}")
    return chosen


def selection_density_tie_break(
    candidate_indices: List[int],
    runs: List[Dict[str, Any]],
    question_idx: Union[int, str] = "?",
) -> Optional[int]:
    """
    Break ties among candidate indices by choosing the run with the highest
    bytes-per-cell density of its dataframe. Falls back to random tie-break
    if density cannot distinguish candidates.
    """
    if not candidate_indices:
        return None

    densities: Dict[int, float] = {}
    for i in candidate_indices:
        df_obj = runs[i].get("df") if isinstance(runs[i], dict) else None
        density_value = -1.0
        if df_obj is not None:
            try:
                rows, cols = df_obj.shape
                denom = rows * cols
                if denom > 0:
                    try:
                        bytes_used = df_obj.memory_usage(deep=True).sum()
                    except Exception:
                        bytes_used = df_obj.memory_usage(deep=False).sum()
                    density_value = float(bytes_used) / float(denom)
            except Exception:
                density_value = -1.0
        densities[i] = density_value

    if not densities:
        return selection_random_tie_break(candidate_indices, question_idx)

    max_density = max(densities.values())
    if max_density <= -1.0:
        # No valid densities computed
        return selection_random_tie_break(candidate_indices, question_idx)

    density_candidates = [i for i, d in densities.items() if d == max_density]
    if len(density_candidates) == 1:
        chosen = density_candidates[0]
        print(
            f"[INFO] [Q{question_idx}] Density tie-break -> picked index {chosen} with density {max_density:.2f}."
        )
        return chosen

    print(
        f"[INFO] [Q{question_idx}] Density tie-break still tied among {len(density_candidates)} candidates."
    )
    return selection_random_tie_break(density_candidates, question_idx)


def selection_size_tie_break(
    candidate_indices: List[int],
    runs: List[Dict[str, Any]],
    question_idx: Union[int, str] = "?",
) -> Optional[int]:
    """
    Break ties among candidate indices by choosing the run with the largest
    DataFrame size (number of elements). Falls back to random tie-break
    if size cannot distinguish candidates or no valid sizes are available.
    """
    if not candidate_indices:
        return None

    sizes: Dict[int, int] = {}
    for i in candidate_indices:
        df_obj = runs[i].get("df") if isinstance(runs[i], dict) else None
        size_value = -1
        if df_obj is not None:
            try:
                size_value = int(df_obj.size)
            except Exception:
                size_value = -1
        sizes[i] = size_value

    if not sizes:
        return selection_random_tie_break(candidate_indices, question_idx)

    max_size = max(sizes.values())
    if max_size <= -1:
        # No valid sizes computed
        return selection_random_tie_break(candidate_indices, question_idx)

    size_candidates = [i for i, s in sizes.items() if s == max_size]
    if len(size_candidates) == 1:
        chosen = size_candidates[0]
        print(
            f"[INFO] [Q{question_idx}] Size tie-break -> picked index {chosen} with size {max_size}."
        )
        return chosen

    print(
        f"[INFO] [Q{question_idx}] Size tie-break still tied among {len(size_candidates)} candidates."
    )
    return selection_random_tie_break(size_candidates, question_idx)


def select_tie_break_index(
    candidate_indices: List[int],
    runs: List[Dict[str, Any]],
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
) -> Optional[int]:
    """
    Central dispatcher for tie-break selection among candidate indices.
    Supported methods: "random" (default), "density", "size".
    Returns the chosen candidate index or None if no candidates provided.
    """
    if not candidate_indices:
        return None
    if len(candidate_indices) == 1:
        return candidate_indices[0]

    method = (tie_break_method or "random").strip().lower()
    if method == "density":
        return selection_density_tie_break(candidate_indices, runs, question_idx)
    if method == "size":
        return selection_size_tie_break(candidate_indices, runs, question_idx)
    return selection_random_tie_break(candidate_indices, question_idx)

def favourite_based_selection(
    all_runs: List[Dict[str, Any]],
    question: str,
    dataset_name: Optional[str],
    db_name: Optional[str],
    question_idx: Union[int, str] = "?",
):
    """
    Selects the Gemini result if available (response not empty and df not None), otherwise Claude (same), otherwise Gradio agent.
    Returns: response, duration, usage, model_name, gen_df_json, generated_sql
    """
    gemini_run = next((r for r in all_runs if r.get("model_name") == "gemini"), None)
    claude_run = next((r for r in all_runs if r.get("model_name") == "claude"), None)

    if gemini_run and gemini_run.get("response") and gemini_run.get("df") is not None:
        print(f"[INFO] [Q{question_idx}] Early match found. Returning Gemini result.")
        return (
            gemini_run.get("response"),
            gemini_run.get("duration"),
            gemini_run.get("usage"),
            gemini_run.get("model_name"),
            gemini_run.get("gen_df_json"),
            gemini_run.get("generated_sql"),
        )

    if claude_run and claude_run.get("response") and claude_run.get("df") is not None:
        print(f"[INFO] [Q{question_idx}] Early match found. Returning Claude result.")
        return (
            claude_run.get("response"),
            claude_run.get("duration"),
            claude_run.get("usage"),
            claude_run.get("model_name"),
            claude_run.get("gen_df_json"),
            claude_run.get("generated_sql"),
        )

    print(f"[INFO] [Q{question_idx}] No Gemini or Claude response with valid DataFrame, calling Gradio agent...")
    start = time.time()
    response = gradio_agent_v2.process_question(
        "http://10.128.0.5:2026/",
        question,
        dataset_name,
        db_name,
        None,
        question_id=question_idx,
        architecture="Multi-Agent Supervisor",
    )
    duration = time.time() - start
    gradio_df = response.get("dataframe") if isinstance(response, dict) else None
    if gradio_df is None:
        print(f"[WARNING] [Q{question_idx}] Gradio agent returned None dataframe. Falling back to random valid run.")
        fallback = rng.choice(all_runs)
        return (
            fallback.get("response"),
            fallback.get("duration"),
            fallback.get("usage"),
            fallback.get("model_name"),
            fallback.get("gen_df_json"),
            fallback.get("generated_sql"),
        )

    gen_df_json = gradio_df.to_json(orient="records", date_format="iso")
    gradio_sql = response.get("generated_sql") if isinstance(response, dict) else None
    duration = duration if duration else claude_run.get("duration") if claude_run else None
    usage = claude_run.get("usage") if claude_run else None
    print(f"[INFO] [Q{question_idx}] Choosing Gradio agent result.")
    return (response, duration, usage, "Gradio agent", gen_df_json, gradio_sql)


def frequency_based_selection(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
):
    consensus: Dict[int, int] = defaultdict(int)
    response_matches: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    model_matches: Dict[str, int] = defaultdict(int)

    for i in range(len(valid_runs)):
        for j in range(i + 1, len(valid_runs)):
            if symetric_compare_df(valid_runs[i]["df"], valid_runs[j]["df"], query_category="a", question=question):
                consensus[i] += 1
                consensus[j] += 1
                model_i = valid_runs[i]["model_name"]
                model_j = valid_runs[j]["model_name"]
                model_matches[model_i] += 1
                model_matches[model_j] += 1
                response_matches[i][model_j] += 1
                response_matches[j][model_i] += 1

    if len(consensus) > 0:
        max_votes = max(consensus.values())
        tied_indices = [i for i, v in consensus.items() if v == max_votes]
        best_index = select_tie_break_index(
            tied_indices, valid_runs, question_idx=question_idx, tie_break_method=tie_break_method
        )
        best = valid_runs[best_index]
        best_matches = response_matches[best_index]
        best_model = best["model_name"]

        match_breakdown = [f"{match_count} {model_name} matches" for model_name, match_count in model_matches.items()]
        response_breakdown = [f"{match_count} {model_name} matches" for model_name, match_count in best_matches.items()]
        consensus_details = " and ".join(match_breakdown)
        response_details = " and ".join(response_breakdown)
        print(
            f"[INFO] [Q{question_idx}] Ensemble selected: {best_model} with {consensus[best_index]} matches. "
            f"{response_details} for the chosen response. {consensus_details} globally. "
        )
        return {
            "response": best.get("response"),
            "duration": best.get("duration"),
            "usage": best.get("usage"),
            "model_name": best.get("model_name"),
            "gen_df_json": best.get("gen_df_json"),
            "generated_sql": best.get("generated_sql"),
            "selected_attempt": best.get("attempt"),
            "selected_row_id": best.get("row_id"),
        }

    gemini_runs = [r for r in valid_runs if r["model_name"] == "gemini"]
    if gemini_runs:
        fallback = rng.choice(gemini_runs)
        print(f"[INFO] [Q{question_idx}] No consensus found. Falling back to Gemini run.")
        return {
            "response": fallback.get("response"),
            "duration": fallback.get("duration"),
            "usage": fallback.get("usage"),
            "model_name": fallback.get("model_name"),
            "gen_df_json": fallback.get("gen_df_json"),
            "generated_sql": fallback.get("generated_sql"),
            "selected_attempt": fallback.get("attempt"),
            "selected_row_id": fallback.get("row_id"),
        }
    else:
        print(f"[WARNING] [Q{question_idx}] No Gemini runs available. Falling back to random valid run.")
        fallback = rng.choice(valid_runs)
        return {
            "response": fallback.get("response"),
            "duration": fallback.get("duration"),
            "usage": fallback.get("usage"),
            "model_name": fallback.get("model_name"),
            "gen_df_json": fallback.get("gen_df_json"),
            "generated_sql": fallback.get("generated_sql"),
            "selected_attempt": fallback.get("attempt"),
            "selected_row_id": fallback.get("row_id"),
        }


def size_based_selection(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
):
    size_dict: Dict[int, int] = defaultdict(int)
    for i in range(len(valid_runs)):
        if "df" in valid_runs[i] and valid_runs[i]["df"] is not None:
            size_dict[i] = valid_runs[i]["df"].size
        else:
            size_dict[i] = -1

    if size_dict and max(size_dict.values()) > -1:
        max_size = max(size_dict.values())
        candidates = [i for i, s in size_dict.items() if s == max_size]
        best_index = select_tie_break_index(
            candidates, valid_runs, question_idx=question_idx, tie_break_method=tie_break_method
        )
        best = valid_runs[best_index]
        print(f"[INFO] [Q{question_idx}] Size-based selection: {best['model_name']} with size {size_dict[best_index]}.")
        return {
            "response": best.get("response"),
            "duration": best.get("duration"),
            "usage": best.get("usage"),
            "model_name": best.get("model_name"),
            "gen_df_json": best.get("gen_df_json"),
            "generated_sql": best.get("generated_sql"),
            "selected_attempt": best.get("attempt"),
            "selected_row_id": best.get("row_id"),
        }
    else:
        print(f"[WARNING] [Q{question_idx}] No valid dataframes found in size_based_selection.")
        return (None, 0.0, None, None, None, None)


def random_based_selection(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
):
    if not valid_runs:
        print(f"[WARNING] [Q{question_idx}] No valid dataframes found in random_based_selection.")
        return (None, 0.0, None, None, None, None)

    # If only one candidate, return it directly
    if len(valid_runs) == 1:
        chosen = valid_runs[0]
        print(f"[INFO] [Q{question_idx}] Random-based selection: single candidate {chosen['model_name']}")
        return {
            "response": chosen.get("response"),
            "duration": chosen.get("duration"),
            "usage": chosen.get("usage"),
            "model_name": chosen.get("model_name"),
            "gen_df_json": chosen.get("gen_df_json"),
            "generated_sql": chosen.get("generated_sql"),
            "selected_attempt": chosen.get("attempt"),
            "selected_row_id": chosen.get("row_id"),
        }

    # Multiple candidates: defer to standard tie-break dispatcher for consistency
    candidate_indices = list(range(len(valid_runs)))
    best_index = select_tie_break_index(
        candidate_indices, valid_runs, question_idx=question_idx, tie_break_method=tie_break_method
    )
    if best_index is None:
        best_index = rng.choice(candidate_indices)
    chosen = valid_runs[best_index]
    print(f"[INFO] [Q{question_idx}] Random-based selection: {chosen['model_name']}")
    return {
        "response": chosen.get("response"),
        "duration": chosen.get("duration"),
        "usage": chosen.get("usage"),
        "model_name": chosen.get("model_name"),
        "gen_df_json": chosen.get("gen_df_json"),
        "generated_sql": chosen.get("generated_sql"),
        "selected_attempt": chosen.get("attempt"),
        "selected_row_id": chosen.get("row_id"),
    }


def binary_comp_selection_singular(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
    signature_rows: int = 10,
):
    """
    Round-robin pairwise comparison like binary_comp_selection but with two modifications:
    - Deduplicate candidates by a canonical signature computed from only the first `signature_rows` rows,
      ignoring column names and column order.
    - Send only the first `signature_rows` rows to the LLM to mitigate quantity bias.
    """
    if not valid_runs:
        print(f"[WARNING] [Q{question_idx}] No valid dataframes found in binary_comp_selection_singular.")
        return (None, 0.0, None, None, None, None)

    # Deduplicate by canonical signature (ignore column names/order; use head rows only)
    signature_to_index: Dict[Tuple[Any, ...], int] = {}
    unique_indices: List[int] = []
    for idx, run in enumerate(valid_runs):
        df_obj = run.get("df") if isinstance(run, dict) else None
        if df_obj is None:
            continue
        sig = _canonical_df_signature(df_obj, num_rows=signature_rows)
        if sig not in signature_to_index:
            signature_to_index[sig] = idx
            unique_indices.append(idx)

    if not unique_indices:
        print(f"[WARNING] [Q{question_idx}] No deduplicated candidates available in binary_comp_selection_singular.")
        return (None, 0.0, None, None, None, None)

    # If only one unique candidate, return it directly
    if len(unique_indices) == 1:
        chosen = valid_runs[unique_indices[0]]
        print(
            f"[INFO] [Q{question_idx}] binary_comp_selection_singular: single unique candidate {chosen.get('model_name')}"
        )
        return {
            "response": chosen.get("response"),
            "duration": chosen.get("duration"),
            "usage": chosen.get("usage"),
            "model_name": chosen.get("model_name"),
            "gen_df_json": chosen.get("gen_df_json"),
            "generated_sql": chosen.get("generated_sql"),
            "selected_attempt": chosen.get("attempt"),
            "selected_row_id": chosen.get("row_id"),
        }

    # Prepare truncated JSON for the unique candidates only
    try:
        from scooring_agents_exp import evaluate_binary_dataframes_with_confidence as llm_evaluate_binary
    except Exception as e:
        print(
            f"[WARNING] [Q{question_idx}] Failed importing binary LLM grader (scooring_agents_exp.evaluate_binary_dataframes_with_confidence): {e}. Falling back to random."
        )
        # Fall back to random among the unique set, using the existing tie-break machinery
        return random_based_selection([valid_runs[i] for i in unique_indices], question, question_idx=question_idx)

    unique_runs: List[Dict[str, Any]] = [valid_runs[i] for i in unique_indices]

    candidates: List[str] = []
    for run in unique_runs:
        candidates.append(
            to_truncated_records_json(
                run.get("gen_df_json"),
                run.get("df"),
                max_rows=signature_rows,
            )
        )

    n = len(candidates)
    scores: List[int] = [0] * n

    # Round-robin pairwise comparisons among unique candidates
    for i in range(n):
        for j in range(i + 1, n):
            try:
                result = llm_evaluate_binary(question, [candidates[i], candidates[j]])
                if isinstance(result, str):
                    result = result.strip()
                    pair_idx = int(result) if result.isdigit() else None
                elif isinstance(result, (int, float)):
                    pair_idx = int(result)
                else:
                    pair_idx = None
            except Exception:
                pair_idx = None

            if pair_idx == 0:
                scores[i] += 1
            elif pair_idx == 1:
                scores[j] += 1
            else:
                # undecided/invalid -> no score change
                pass

    max_score = max(scores) if scores else -1
    tied_indices = [idx for idx, s in enumerate(scores) if s == max_score]

    if len(tied_indices) == 1:
        best_unique_index = tied_indices[0]
    else:
        # Use existing tie-break over the unique subset
        best_unique_index = select_tie_break_index(
            tied_indices, unique_runs, question_idx=question_idx, tie_break_method=tie_break_method
        )
        if best_unique_index is None:
            best_unique_index = rng.choice(tied_indices)

    best = unique_runs[best_unique_index]
    print(
        f"[INFO] [Q{question_idx}] binary_comp_selection_singular selected: {best.get('model_name')} (unique candidate #{best_unique_index}) with score {max_score}."
    )
    return {
        "response": best.get("response"),
        "duration": best.get("duration"),
        "usage": best.get("usage"),
        "model_name": best.get("model_name"),
        "gen_df_json": best.get("gen_df_json"),
        "generated_sql": best.get("generated_sql"),
        "selected_attempt": best.get("attempt"),
        "selected_row_id": best.get("row_id"),
    }


def density_based_selection(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
):
    density_dict: Dict[int, float] = defaultdict(float)
    for i in range(len(valid_runs)):
        df_obj = valid_runs[i].get("df") if isinstance(valid_runs[i], dict) else None
        if df_obj is not None:
            try:
                rows, cols = df_obj.shape
                denom = rows * cols
                if denom > 0:
                    try:
                        bytes_used = df_obj.memory_usage(deep=True).sum()
                    except Exception:
                        bytes_used = df_obj.memory_usage(deep=False).sum()
                    density_value = float(bytes_used) / float(denom)
                    density_dict[i] = density_value
                else:
                    density_dict[i] = -1.0
            except Exception:
                density_dict[i] = -1.0
        else:
            density_dict[i] = -1.0

    if density_dict and max(density_dict.values()) > -1:
        max_density = max(density_dict.values())
        candidates = [i for i, d in density_dict.items() if d == max_density]
        best_index = select_tie_break_index(
            candidates, valid_runs, question_idx=question_idx, tie_break_method=tie_break_method
        )
        best = valid_runs[best_index]
        print(
            f"[INFO] [Q{question_idx}] Density-based selection: {best['model_name']} with density {density_dict[best_index]:.2f} bytes/cell."
        )
        return {
            "response": best.get("response"),
            "duration": best.get("duration"),
            "usage": best.get("usage"),
            "model_name": best.get("model_name"),
            "gen_df_json": best.get("gen_df_json"),
            "generated_sql": best.get("generated_sql"),
            "selected_attempt": best.get("attempt"),
            "selected_row_id": best.get("row_id"),
        }
    else:
        print(f"[WARNING] [Q{question_idx}] No valid dataframes found in density_based_selection.")
        return (None, 0.0, None, None, None, None)


def reverse_size_based_selection(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
):
    """
    Select candidate with the SMALLEST DataFrame size (> -1). Falls back when none valid.
    """
    size_dict: Dict[int, int] = defaultdict(int)
    for i in range(len(valid_runs)):
        if "df" in valid_runs[i] and valid_runs[i]["df"] is not None:
            try:
                size_dict[i] = int(valid_runs[i]["df"].size)
            except Exception:
                size_dict[i] = -1
        else:
            size_dict[i] = -1

    # Filter to valid sizes (> -1)
    valid_sizes = [s for s in size_dict.values() if s > -1]
    if size_dict and len(valid_sizes) > 0:
        min_size = min(valid_sizes)
        candidates = [i for i, s in size_dict.items() if s == min_size]
        best_index = select_tie_break_index(
            candidates, valid_runs, question_idx=question_idx, tie_break_method=tie_break_method
        )
        best = valid_runs[best_index]
        print(f"[INFO] [Q{question_idx}] Reverse size-based selection: {best['model_name']} with size {size_dict[best_index]}.")
        return {
            "response": best.get("response"),
            "duration": best.get("duration"),
            "usage": best.get("usage"),
            "model_name": best.get("model_name"),
            "gen_df_json": best.get("gen_df_json"),
            "generated_sql": best.get("generated_sql"),
            "selected_attempt": best.get("attempt"),
            "selected_row_id": best.get("row_id"),
        }
    else:
        print(f"[WARNING] [Q{question_idx}] No valid dataframes found in reverse_size_based_selection.")
        return (None, 0.0, None, None, None, None)


def reverse_density_based_selection(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
):
    """
    Select candidate with the LOWEST bytes-per-cell density (> -1). Falls back when none valid.
    """
    density_dict: Dict[int, float] = defaultdict(float)
    for i in range(len(valid_runs)):
        df_obj = valid_runs[i].get("df") if isinstance(valid_runs[i], dict) else None
        if df_obj is not None:
            try:
                rows, cols = df_obj.shape
                denom = rows * cols
                if denom > 0:
                    try:
                        bytes_used = df_obj.memory_usage(deep=True).sum()
                    except Exception:
                        bytes_used = df_obj.memory_usage(deep=False).sum()
                    density_value = float(bytes_used) / float(denom)
                    density_dict[i] = density_value
                else:
                    density_dict[i] = -1.0
            except Exception:
                density_dict[i] = -1.0
        else:
            density_dict[i] = -1.0

    # Filter to valid densities (> -1)
    valid_densities = [d for d in density_dict.values() if d > -1]
    if density_dict and len(valid_densities) > 0:
        min_density = min(valid_densities)
        candidates = [i for i, d in density_dict.items() if d == min_density]
        best_index = select_tie_break_index(
            candidates, valid_runs, question_idx=question_idx, tie_break_method=tie_break_method
        )
        best = valid_runs[best_index]
        print(
            f"[INFO] [Q{question_idx}] Reverse density-based selection: {best['model_name']} with density {density_dict[best_index]:.2f} bytes/cell."
        )
        return {
            "response": best.get("response"),
            "duration": best.get("duration"),
            "usage": best.get("usage"),
            "model_name": best.get("model_name"),
            "gen_df_json": best.get("gen_df_json"),
            "generated_sql": best.get("generated_sql"),
            "selected_attempt": best.get("attempt"),
            "selected_row_id": best.get("row_id"),
        }
    else:
        print(f"[WARNING] [Q{question_idx}] No valid dataframes found in reverse_density_based_selection.")
        return (None, 0.0, None, None, None, None)


def reverse_frequency_based_selection(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
):
    """
    Select the candidate with the FEWEST consensus matches across pairs.
    """
    consensus: Dict[int, int] = defaultdict(int)

    for i in range(len(valid_runs)):
        for j in range(i + 1, len(valid_runs)):
            try:
                if symetric_compare_df(valid_runs[i]["df"], valid_runs[j]["df"], query_category="a", question=question):
                    consensus[i] += 1
                    consensus[j] += 1
            except Exception:
                # Ignore comparison failures; treat as no match contributing to lower consensus
                pass

    if len(consensus) > 0:
        # Consider all indices present in valid_runs even if absent from consensus dict (default 0)
        for idx in range(len(valid_runs)):
            if idx not in consensus:
                consensus[idx] = 0
        min_votes = min(consensus.values())
        tied_indices = [i for i, v in consensus.items() if v == min_votes]
        best_index = select_tie_break_index(
            tied_indices, valid_runs, question_idx=question_idx, tie_break_method=tie_break_method
        )
        best = valid_runs[best_index]
        print(
            f"[INFO] [Q{question_idx}] Reverse frequency-based selection: {best['model_name']} with {consensus[best_index]} matches (lowest)."
        )
        return {
            "response": best.get("response"),
            "duration": best.get("duration"),
            "usage": best.get("usage"),
            "model_name": best.get("model_name"),
            "gen_df_json": best.get("gen_df_json"),
            "generated_sql": best.get("generated_sql"),
            "selected_attempt": best.get("attempt"),
            "selected_row_id": best.get("row_id"),
        }
    else:
        # If consensus empty (shouldn't happen with any valid_runs), fall back to random
        print(f"[WARNING] [Q{question_idx}] No consensus computed in reverse_frequency_based_selection. Falling back to random.")
        return random_based_selection(valid_runs, question, question_idx=question_idx)


def agent_indiv_grade_selection(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
):
    """
    Use LLM-based grading from scooring.evaluate_dataframes to select the best candidate.
    Falls back to random selection if grading fails for any reason.
    """
    if not valid_runs:
        print(f"[WARNING] [Q{question_idx}] No valid dataframes found in agent_indiv_grade_selection.")
        return (None, 0.0, None, None, None, None)

    try:
        # Import lazily to avoid heavy deps unless method is actually used
        from scooring_agents_exp import evaluate_single_dataframe as llm_evaluate_single
    except Exception as e:
        print(
            f"[WARNING] [Q{question_idx}] Failed importing LLM grader (scooring.evaluate_dataframes): {e}. Falling back to random."
        )
        return random_based_selection(valid_runs, question, question_idx=question_idx)

    # Build list of candidate JSON strings for grading (truncate to <= MAX_LLM_ROWS)
    candidates: List[str] = []
    for run in valid_runs:
        candidates.append(
            to_truncated_records_json(
                run.get("gen_df_json"),
                run.get("df"),
                max_rows=MAX_LLM_ROWS,
            )
        )

    try:
        # Score each candidate individually using the LLM grader
        scores: List[int] = []
        for df_json in candidates:
            try:
                score_val = llm_evaluate_single(question, df_json)
                if not isinstance(score_val, (int, float)):
                    score_val = -1
            except Exception:
                score_val = -1
            scores.append(int(score_val))

        if not scores:
            return random_based_selection(valid_runs, question, question_idx=question_idx)

        max_score = max(scores)
        tied_indices = [i for i, s in enumerate(scores) if s == max_score]

        if len(tied_indices) == 1:
            best_index = tied_indices[0]
        else:
            # Resolve ties according to requested tie_break_method using existing tie-break helpers
            best_index = select_tie_break_index(
                tied_indices, valid_runs, question_idx=question_idx, tie_break_method=tie_break_method
            )
            if best_index is None:
                best_index = rng.choice(tied_indices)

        best = valid_runs[best_index]
        print(
            f"[INFO] [Q{question_idx}] agent_indiv_grade selected: {best.get('model_name')} (candidate #{best_index}) with score {max_score}."
        )
        return {
            "response": best.get("response"),
            "duration": best.get("duration"),
            "usage": best.get("usage"),
            "model_name": best.get("model_name"),
            "gen_df_json": best.get("gen_df_json"),
            "generated_sql": best.get("generated_sql"),
            "selected_attempt": best.get("attempt"),
            "selected_row_id": best.get("row_id"),
        }
    except Exception as e:
        print(
            f"[WARNING] [Q{question_idx}] LLM grading failed in agent_indiv_grade_selection: {e}. Falling back to random."
        )
        return random_based_selection(valid_runs, question, question_idx=question_idx)


def binary_comp_selection(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
):
    """
    Round-robin pairwise comparison using LLM binary evaluator from scooring_agents_exp.
    Each candidate gains +1 score for every other candidate it wins against.
    The highest total score wins; ties are resolved via the configured tie-breaker.
    """
    if not valid_runs:
        print(f"[WARNING] [Q{question_idx}] No valid dataframes found in binary_comp_selection.")
        return (None, 0.0, None, None, None, None)

    # Lazy import to avoid heavy deps unless used
    try:
        from scooring_agents_exp import evaluate_binary_dataframes_with_confidence as llm_evaluate_binary
    except Exception as e:
        print(
            f"[WARNING] [Q{question_idx}] Failed importing binary LLM grader (scooring_agents_exp.evaluate_binary_dataframes_with_confidence): {e}. Falling back to random."
        )
        return random_based_selection(valid_runs, question, question_idx=question_idx)

    # Prepare JSON strings for each candidate (truncate to <= MAX_LLM_ROWS)
    candidates: List[str] = []
    for run in valid_runs:
        candidates.append(
            to_truncated_records_json(
                run.get("gen_df_json"),
                run.get("df"),
                max_rows=MAX_LLM_ROWS,
            )
        )

    n = len(candidates)
    if n == 1:
        best = valid_runs[0]
        print(f"[INFO] [Q{question_idx}] binary_comp_selection: single candidate {best.get('model_name')}")
        return {
            "response": best.get("response"),
            "duration": best.get("duration"),
            "usage": best.get("usage"),
            "model_name": best.get("model_name"),
            "gen_df_json": best.get("gen_df_json"),
            "generated_sql": best.get("generated_sql"),
            "selected_attempt": best.get("attempt"),
            "selected_row_id": best.get("row_id"),
        }

    scores: List[int] = [0] * n

    # Round-robin pairwise comparisons
    for i in range(n):
        for j in range(i + 1, n):
            try:
                result = llm_evaluate_binary(question, [candidates[i], candidates[j]])
                # result may be string or int; map 0->i wins, 1->j wins
                if isinstance(result, str):
                    result = result.strip()
                    pair_idx = int(result) if result.isdigit() else None
                elif isinstance(result, (int, float)):
                    pair_idx = int(result)
                else:
                    pair_idx = None
            except Exception:
                pair_idx = None

            if pair_idx == 0:
                scores[i] += 1
            elif pair_idx == 1:
                scores[j] += 1
            else:
                # Ignore invalid/undecided outcomes; rely on tie-breaker later
                pass

    max_score = max(scores) if scores else -1
    tied_indices = [idx for idx, s in enumerate(scores) if s == max_score]

    if len(tied_indices) == 1:
        best_index = tied_indices[0]
    else:
        # Resolve ties using existing tie-break helpers
        best_index = select_tie_break_index(
            tied_indices, valid_runs, question_idx=question_idx, tie_break_method=tie_break_method
        )
        if best_index is None:
            best_index = rng.choice(tied_indices)

    best = valid_runs[best_index]
    print(
        f"[INFO] [Q{question_idx}] binary_comp_selection selected: {best.get('model_name')} (candidate #{best_index}) with score {max_score}."
    )
    return {
        "response": best.get("response"),
        "duration": best.get("duration"),
        "usage": best.get("usage"),
        "model_name": best.get("model_name"),
        "gen_df_json": best.get("gen_df_json"),
        "generated_sql": best.get("generated_sql"),
        "selected_attempt": best.get("attempt"),
        "selected_row_id": best.get("row_id"),
    }


def double_elim_selection(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
    n: int = 5,
):
    """
    Run a double-elimination tournament among candidates using LLM binary evaluation.

    - Seeds are randomized in position using a seeded RNG (global rng).
    - Each match compares two candidates via scooring_agents_exp.evaluate_binary_dataframes_with_confidence.
    - A candidate is eliminated after two losses. Last remaining wins.
    """
    if not valid_runs:
        print(f"[WARNING] [Q{question_idx}] No valid dataframes found in double_elim_selection.")
        return (None, 0.0, None, None, None, None)

    # Lazy import to avoid heavy deps unless used
    try:
        from scooring_agents_exp import evaluate_binary_dataframes_with_confidence as llm_evaluate_binary
    except Exception as e:
        print(
            f"[WARNING] [Q{question_idx}] Failed importing LLM binary grader (scooring_agents_exp.evaluate_binary_dataframes_with_confidence): {e}. Falling back to random."
        )
        return random_based_selection(valid_runs, question, question_idx=question_idx)

    # Build JSON strings for each candidate (truncate to <= MAX_LLM_ROWS)
    candidates_json: List[str] = []
    for run in valid_runs:
        candidates_json.append(
            to_truncated_records_json(
                run.get("gen_df_json"),
                run.get("df"),
                max_rows=MAX_LLM_ROWS,
            )
        )

    num_candidates = len(candidates_json)
    if num_candidates == 1:
        best = valid_runs[0]
        print(f"[INFO] [Q{question_idx}] double_elim_selection: single candidate {best.get('model_name')}")
        return {
            "response": best.get("response"),
            "duration": best.get("duration"),
            "usage": best.get("usage"),
            "model_name": best.get("model_name"),
            "gen_df_json": best.get("gen_df_json"),
            "generated_sql": best.get("generated_sql"),
            "selected_attempt": best.get("attempt"),
            "selected_row_id": best.get("row_id"),
        }

    def run_bracket_once(t: int) -> int:
        # Local deterministic RNG per tournament to vary brackets across n while reproducible
        try:
            q_hash = hash(str(question_idx)) & 0xFFFFFFFF
        except Exception:
            q_hash = 0
        # Use a golden-ratio step to decorrelate
        t_salt = (t * 0x9E3779B9) & 0xFFFFFFFF
        seed_value = (RNG_SEED ^ q_hash ^ t_salt) & 0xFFFFFFFF
        rng_local = random.Random(seed_value)

        # Initialize loss counts and randomized seeding for this tournament
        indices: List[int] = list(range(num_candidates))
        rng_local.shuffle(indices)
        loss_count: Dict[int, int] = {i: 0 for i in indices}

        def active_contenders() -> List[int]:
            return [i for i in indices if loss_count.get(i, 0) < 2]

        def play_match(i: int, j: int) -> Tuple[int, int]:
            """Return (winner_idx, loser_idx) among original indices i, j."""
            try:
                result_idx = llm_evaluate_binary(question, [candidates_json[i], candidates_json[j]])
                try:
                    pair_idx = int(result_idx)
                except Exception:
                    pair_idx = None
            except Exception:
                pair_idx = None

            if pair_idx == 0:
                return i, j
            if pair_idx == 1:
                return j, i
            # On undecided, pick via per-tournament RNG for determinism with variety across n
            chosen = rng_local.choice([0, 1])
            return (i, j) if chosen == 0 else (j, i)

        safety_counter = 0
        while True:
            alive = active_contenders()
            if len(alive) <= 1:
                break
            # Randomize pairing order each round (per-tournament RNG)
            rng_local.shuffle(alive)
            # Pair adjacent; odd one gets bye
            round_pairs: List[Tuple[int, int]] = []
            k = 0
            while k + 1 < len(alive):
                round_pairs.append((alive[k], alive[k + 1]))
                k += 2
            # Process matches
            for a, b in round_pairs:
                winner, loser = play_match(a, b)
                loss_count[loser] = loss_count.get(loser, 0) + 1
            # Safety to avoid infinite loops on pathological cases
            safety_counter += 1
            if safety_counter > (num_candidates * 10):
                print(f"[WARNING] [Q{question_idx}] Safety break in double_elim_selection after {safety_counter} rounds.")
                break

        # Determine winner among remaining contenders (prefer lowest losses)
        remaining = [i for i in indices if loss_count.get(i, 0) < 2]
        if not remaining:
            min_losses = min(loss_count.values()) if loss_count else 2
            cands = [i for i, l in loss_count.items() if l == min_losses]
            return rng_local.choice(cands) if cands else rng_local.choice(list(range(num_candidates)))
        return remaining[0]

    # Run the tournament n times and collect winners
    winners: List[int] = []
    try:
        total_runs = int(n) if isinstance(n, (int, float, str)) else 5
    except Exception:
        total_runs = 5
    total_runs = max(1, int(total_runs))
    for t in range(total_runs):
        winners.append(run_bracket_once(t))

    # If a single winner across all runs, pick it; otherwise use tie-breaker
    if len(set(winners)) == 1:
        winner_i = winners[0]
    else:
        # Pass the list (allowing duplicates) to tie-breaker for random weighting; others dedup internally
        winner_i = select_tie_break_index(winners, valid_runs, question_idx=question_idx, tie_break_method=tie_break_method)
        if winner_i is None:
            winner_i = rng.choice(winners)

    best = valid_runs[winner_i]
    print(
        f"[INFO] [Q{question_idx}] double_elim_selection selected: {best.get('model_name')} (candidate #{winner_i}) from {total_runs} tournaments."
    )
    return {
        "response": best.get("response"),
        "duration": best.get("duration"),
        "usage": best.get("usage"),
        "model_name": best.get("model_name"),
        "gen_df_json": best.get("gen_df_json"),
        "generated_sql": best.get("generated_sql"),
        "selected_attempt": best.get("attempt"),
        "selected_row_id": best.get("row_id"),
    }


def binary_comp_sql_selection(
    valid_runs: List[Dict[str, Any]],
    question: str,
    question_idx: Union[int, str] = "?",
    tie_break_method: str = "random",
):
    """
    Pairwise comparison using LLM binary evaluator with SQL context.
    Each candidate gains +1 per victory against others. Highest total wins.
    """
    if not valid_runs:
        print(f"[WARNING] [Q{question_idx}] No valid dataframes found in binary_comp_sql_selection.")
        return (None, 0.0, None, None, None, None)

    try:
        from scooring_agents_exp import evaluate_binary_dataframes_with_confidence_sql as llm_eval_sql
    except Exception as e:
        print(
            f"[WARNING] [Q{question_idx}] Failed importing SQL-aware LLM grader (evaluate_binary_dataframes_with_confidence_sql): {e}. Falling back to binary_comp_selection."
        )
        return binary_comp_selection(valid_runs, question, question_idx=question_idx, tie_break_method=tie_break_method)

    # Prepare inputs (truncate DF JSON as usual) and collect SQL strings
    df_candidates: List[str] = []
    sql_candidates: List[str] = []
    for run in valid_runs:
        df_candidates.append(
            to_truncated_records_json(
                run.get("gen_df_json"),
                run.get("df"),
                max_rows=MAX_LLM_ROWS,
            )
        )
        sql_candidates.append(run.get("generated_sql"))

    n = len(df_candidates)
    if n == 1:
        best = valid_runs[0]
        print(f"[INFO] [Q{question_idx}] binary_comp_sql_selection: single candidate {best.get('model_name')}")
        return {
            "response": best.get("response"),
            "duration": best.get("duration"),
            "usage": best.get("usage"),
            "model_name": best.get("model_name"),
            "gen_df_json": best.get("gen_df_json"),
            "generated_sql": best.get("generated_sql"),
            "selected_attempt": best.get("attempt"),
            "selected_row_id": best.get("row_id"),
        }

    scores: List[int] = [0] * n

    # Round-robin pairwise comparisons
    for i in range(n):
        for j in range(i + 1, n):
            try:
                result = llm_eval_sql(
                    question,
                    [df_candidates[i], df_candidates[j]],
                    sql_list=[sql_candidates[i], sql_candidates[j]],
                )
                if isinstance(result, str):
                    s = result.strip()
                    pair_idx = int(s) if s.isdigit() else None
                elif isinstance(result, (int, float)):
                    pair_idx = int(result)
                else:
                    pair_idx = None
            except Exception:
                pair_idx = None

            if pair_idx == 0:
                scores[i] += 1
            elif pair_idx == 1:
                scores[j] += 1
            else:
                pass

    max_score = max(scores) if scores else -1
    tied_indices = [idx for idx, s in enumerate(scores) if s == max_score]

    if len(tied_indices) == 1:
        best_index = tied_indices[0]
    else:
        best_index = select_tie_break_index(
            tied_indices, valid_runs, question_idx=question_idx, tie_break_method=tie_break_method
        )
        if best_index is None:
            best_index = rng.choice(tied_indices)

    best = valid_runs[best_index]
    print(
        f"[INFO] [Q{question_idx}] binary_comp_sql_selection selected: {best.get('model_name')} (candidate #{best_index}) with score {max_score}."
    )
    return {
        "response": best.get("response"),
        "duration": best.get("duration"),
        "usage": best.get("usage"),
        "model_name": best.get("model_name"),
        "gen_df_json": best.get("gen_df_json"),
        "generated_sql": best.get("generated_sql"),
        "selected_attempt": best.get("attempt"),
        "selected_row_id": best.get("row_id"),
    }

def ensemble_result(
    mlflow_run_id: Optional[str],
    all_runs: List[Dict[str, Any]],
    question: str,
    dataset_name: Optional[str],
    db_name: Optional[str],
    question_idx: Union[int, str] = "?",
    ensemble_selection_method: str = "size",
    use_gradio_agent: bool = True,
    tie_break_method: str = "random",
    double_elim_n: Optional[int] = None,
):
    """
    Uses dataframe comparison to select the most consistent output.
    Returns one of the selection tuples, typically 6-tuple: (response, duration, usage, model_name, gen_df_json, generated_sql)
    """
    print(f"[INFO] [Q{question_idx}] Running ensemble selection with method '{ensemble_selection_method}'")
    if ensemble_selection_method == "favourite":
        dataset_name = all_runs[0].get("dataset_name") if all_runs and "dataset_name" in all_runs[0] else None
        db_name = all_runs[0].get("db_name") if all_runs and "db_name" in all_runs[0] else None
        print(f"[INFO] [Q{question_idx}] Favourite-based selection")
        return favourite_based_selection(all_runs, question, dataset_name, db_name, question_idx=question_idx)

    valid_runs = [r for r in all_runs if r.get("df") is not None]
    if not valid_runs:
        if use_gradio_agent:
            print(f"[WARNING] [Q{question_idx}] No valid dataframes to ensemble. Calling Gradio agent...")
            print(f"Dataset name: {dataset_name}")
            start = time.time()
            response = gradio_agent_v2.process_question(
                "http://10.128.0.5:2026/",
                question,
                "BIRD",
                db_name,
                mlflow_run_id,
                question_id=question_idx,
                architecture="SQLATS",
            )
            duration = time.time() - start
            gradio_df = response.get("dataframe") if isinstance(response, dict) else None
            gradio_sql = response.get("generated_sql") if isinstance(response, dict) else None
            if gradio_df is None:
                print(f"[WARNING] [Q{question_idx}] Gradio agent returned None dataframe. Falling back to random valid run.")
                fallback_runs = [r for r in all_runs if r.get("response")]
                fallback = rng.choice(fallback_runs) if fallback_runs else None
                if fallback:
                    return (
                        fallback.get("response"),
                        fallback.get("duration"),
                        fallback.get("usage"),
                        fallback.get("model_name"),
                        fallback.get("gen_df_json"),
                        fallback.get("generated_sql"),
                    )
                else:
                    print(f"[ERROR] [Q{question_idx}] No valid fallback run found.")
                    return (None, 0.0, None, None, None, None)

            gen_df_json = gradio_df.to_json(orient="records", date_format="iso")
            gemini_run = next((r for r in all_runs if r.get("model_name") == "gemini"), None)
            usage = gemini_run.get("usage") if gemini_run else None
            print(f"[INFO] [Q{question_idx}] Choosing Gradio agent result.")
            return (response, duration, usage, "Gradio agent", gen_df_json, gradio_sql)
        else:
            print(f"[WARNING] [Q{question_idx}] No valid dataframes to ensemble.")
            for r in all_runs:
                if r.get("response"):
                    print(f"[INFO] Using raw response from {r['model_name']} despite no DF.")
                    return (r["response"], r.get("duration"), r.get("usage"), r.get("model_name"), None, None)
            return (None, 0.0, None, None, None, None)

    if ensemble_selection_method == "size":
        print(f"[INFO] [Q{question_idx}] Size-based selection")
        return size_based_selection(valid_runs, question, question_idx=question_idx, tie_break_method=tie_break_method)
    elif ensemble_selection_method == "frequency":
        print(f"[INFO] [Q{question_idx}] Frequency-based selection")
        return frequency_based_selection(valid_runs, question, question_idx=question_idx, tie_break_method=tie_break_method)
    elif ensemble_selection_method == "random":
        print(f"[INFO] [Q{question_idx}] Random-based selection")
        return random_based_selection(valid_runs, question, question_idx=question_idx)
    elif ensemble_selection_method == "density":
        print(f"[INFO] [Q{question_idx}] Density-based selection")
        return density_based_selection(valid_runs, question, question_idx=question_idx, tie_break_method=tie_break_method)
    elif ensemble_selection_method == "reverse_size":
        print(f"[INFO] [Q{question_idx}] Reverse size-based selection")
        return reverse_size_based_selection(valid_runs, question, question_idx=question_idx, tie_break_method=tie_break_method)
    elif ensemble_selection_method == "reverse_density":
        print(f"[INFO] [Q{question_idx}] Reverse density-based selection")
        return reverse_density_based_selection(valid_runs, question, question_idx=question_idx, tie_break_method=tie_break_method)
    elif ensemble_selection_method == "reverse_frequency":
        print(f"[INFO] [Q{question_idx}] Reverse frequency-based selection")
        return reverse_frequency_based_selection(valid_runs, question, question_idx=question_idx, tie_break_method=tie_break_method)
    elif ensemble_selection_method == "agent_indiv_grade":
        print(f"[INFO] [Q{question_idx}] Agent-individual-grade selection (LLM)" )
        return agent_indiv_grade_selection(valid_runs, question, question_idx=question_idx, tie_break_method=tie_break_method)
    elif ensemble_selection_method == "binary_comp_selection":
        print(f"[INFO] [Q{question_idx}] Binary-comp selection (pairwise LLM)" )
        return binary_comp_selection(valid_runs, question, question_idx=question_idx, tie_break_method=tie_break_method)
    elif ensemble_selection_method == "binary_comp_selection_singular":
        print(f"[INFO] [Q{question_idx}] Binary-comp selection singular (dedup + head-only LLM)")
        return binary_comp_selection_singular(
            valid_runs,
            question,
            question_idx=question_idx,
            tie_break_method=tie_break_method,
        )
    elif ensemble_selection_method == "binary_comp_sql":
        print(f"[INFO] [Q{question_idx}] Binary-comp selection with SQL context")
        return binary_comp_sql_selection(
            valid_runs,
            question,
            question_idx=question_idx,
            tie_break_method=tie_break_method,
        )
    elif ensemble_selection_method == "double_elim":
        print(f"[INFO] [Q{question_idx}] Double-elimination selection (LLM binary)")
        return double_elim_selection(
            valid_runs,
            question,
            question_idx=question_idx,
            tie_break_method=tie_break_method,
            n=(double_elim_n if double_elim_n is not None else 1),
        )
    else:
        print(
            f"[WARNING] [Q{question_idx}] Unknown ensemble selection method '{ensemble_selection_method}', defaulting to size."
        )
        return size_based_selection(valid_runs, question, question_idx=question_idx, tie_break_method=tie_break_method)


def _row_to_run_dict(row: Dict[str, Any], row_index: Optional[Any] = None) -> Dict[str, Any]:
    """
    Convert a row from an all_runs-style DataFrame into the internal run dict
    expected by the ensemble selection functions.
    """
    df_obj = None
    gen_df_json = row.get("gen_df_json", None)
    if isinstance(gen_df_json, str) and len(gen_df_json.strip()) > 0 and gen_df_json.strip().lower() != "nan":
        try:
            df_obj = pd.DataFrame(json.loads(gen_df_json))
        except Exception:
            try:
                cleaned = gen_df_json.replace("\n", "").replace("\r", "")
                df_obj = pd.DataFrame(json.loads(cleaned))
            except Exception:
                df_obj = None

    return {
        "question_index": row.get("question_index", row.get("question_id", "?")),
        "question": row.get("question", None),
        "model_name": row.get("model_name", None),
        "attempt": row.get("attempt", 0),
        "response": row.get("response", None),
        "code": row.get("extracted_python_code", row.get("code", None)),
        "duration": row.get("duration", row.get("execution_time", None)),
        "usage": row.get("usage", None),
        "df": df_obj,
        "gen_df_json": gen_df_json if isinstance(gen_df_json, str) else None,
        "sql": row.get("sql", ""),
        "generated_sql": row.get("generated_sql", row.get("gen_sql", None)),
        "dataset_name": row.get("dataset_name", None),
        "db_name": row.get("db_name", None),
        "row_id": (row_index if row_index is not None else getattr(row, "name", None)),
    }


def _normalize_ensemble_output(ret: Union[Dict[str, Any], List[Any], Tuple[Any, ...], Any]):
    """
    Normalize variable-length outputs from ensemble_result into a fixed 6-tuple:
    (response, duration, usage, model_name, gen_df_json, generated_sql)
    """
    if isinstance(ret, dict):
        return (
            ret.get("response"),
            ret.get("execution_time"),
            ret.get("usage"),
            ret.get("model_name"),
            ret.get("gen_df_json"),
            ret.get("gen_sql") if ret.get("gen_sql") is not None else ret.get("generated_sql"),
        )
    if isinstance(ret, (list, tuple)):
        items: List[Any] = list(ret)
        if len(items) < 6:
            items += [None] * (6 - len(items))
        return tuple(items[:6])
    return (ret, None, None, None, None, None)


def ensemble_from_all_runs_df(
    all_runs_df: pd.DataFrame,
    ensemble_selection_method: str = "size",
    use_gradio_agent: bool = False,
    mlflow_run_id: Optional[str] = None,
    tie_break_method: str = "random",
    double_elim_n: Optional[int] = None,
) -> pd.DataFrame:
    """
    Run ensemble selection per question group from an all_runs-style DataFrame.
    Returns a DataFrame with one row per question group containing the chosen response and associated metadata.
    """
    candidate_keys = [
        ["question", "dataset_name", "db_name", "question_index"],
        ["question", "dataset_name", "db_name"],
        ["question", "db_name"],
        ["question"],
    ]
    group_keys = None
    for keys in candidate_keys:
        if all(k in all_runs_df.columns for k in keys):
            group_keys = keys
            break
    if group_keys is None:
        raise ValueError("all_runs DataFrame lacks required columns to group by question")

    winners: List[Dict[str, Any]] = []
    for group_values, group_df in all_runs_df.groupby(group_keys):
        if not isinstance(group_values, tuple):
            group_values = (group_values,)
        group_dict = dict(zip(group_keys, group_values))
        question = group_dict.get("question", None)
        dataset_name = group_dict.get("dataset_name", None)
        db_name = group_dict.get("db_name", None)
        q_index = group_dict.get("question_index", "?")

        runs = [_row_to_run_dict(row, row_index=idx) for idx, row in group_df.iterrows()]

        _ret = ensemble_result(
            mlflow_run_id,
            runs,
            question,
            dataset_name,
            db_name,
            question_idx=q_index,
            ensemble_selection_method=ensemble_selection_method,
            use_gradio_agent=use_gradio_agent,
            tie_break_method=tie_break_method,
            double_elim_n=double_elim_n,
        )
        if isinstance(_ret, dict):
            response = _ret.get("response")
            duration = _ret.get("duration")
            usage = _ret.get("usage")
            model_name = _ret.get("model_name")
            gen_df_json = _ret.get("gen_df_json")
            generated_sql = _ret.get("generated_sql") or _ret.get("gen_sql")
            selected_attempt = _ret.get("selected_attempt")
            selected_row_id = _ret.get("selected_row_id")
        else:
            response, duration, usage, model_name, gen_df_json, generated_sql = _normalize_ensemble_output(_ret)
            selected_attempt = None
            selected_row_id = None

        winners.append(
            {
                "question": question,
                "dataset_name": dataset_name,
                "db_name": db_name,
                "question_index": q_index,
                "sql": (group_df["sql"].iloc[0] if "sql" in group_df.columns else None),
                "response": response,
                "execution_time": duration,
                "usage": usage,
                "model_name": model_name,
                "gen_df_json": gen_df_json,
                "gen_sql": generated_sql,
                "selected_attempt": selected_attempt,
                "selected_row_id": selected_row_id,
            }
        )

    return pd.DataFrame(winners)


def ensemble_from_all_runs_file(
    all_runs_path: str,
    ensemble_selection_method: str = "size",
    use_gradio_agent: bool = False,
    output_dir: Optional[str] = None,
    mlflow_run_id: Optional[str] = None,
    tie_break_method: str = "random",
    double_elim_n: Optional[int] = None,
):
    """
    Convenience wrapper to run ensemble from an all_runs CSV file.
    Returns winners_df and optionally writes a CSV to output_dir.
    """
    df = pd.read_csv(all_runs_path)
    winners_df = ensemble_from_all_runs_df(
        df,
        ensemble_selection_method=ensemble_selection_method,
        use_gradio_agent=use_gradio_agent,
        mlflow_run_id=mlflow_run_id,
        tie_break_method=tie_break_method,
        double_elim_n=double_elim_n,
    )

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(
            output_dir, f"ensemble_from_all_runs_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
        )
        winners_df.to_csv(output_file, index=False)
        return winners_df, output_file
    return winners_df, None


