#!/usr/bin/env python3
"""
Script to evaluate all_runs files using test_data.eval functions.
This script processes the all_runs CSV file and determines if each result is a match, no match, or query error.

Outputs:
1. An identical CSV as the input CSV but with an extra column that indicates if the row was match, no_match or query error.
2. A CSV with each unique question ID and a has_match column that is TRUE only if any one result of that same question ID came up as true
"""

import argparse
import pandas as pd
import os
import sys
from datetime import datetime
import logging
import json
import re
try:
    import mlflow
except Exception:
    mlflow = None
try:
    from dotenv import load_dotenv
    from pathlib import Path
except Exception:
    load_dotenv = None
# Progress bar (removed; no runtime execution loop)

# Ensemble logic
from ensemble_logic import ensemble_from_all_runs_df

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _normalize_eval_result_to_comparison(value: str) -> str:
    """Normalize eval_result values into comparison_result categories.

    Output space: 'Match', 'No Match', 'Query Error'.
    """
    if value is None:
        return 'Query Error'
    text = str(value).strip()
    if text.lower() == 'match':
        return 'Match'
    if text.replace(' ', '').lower() == 'nomatch':
        return 'No Match'
    if text.lower() == 'no match':
        return 'No Match'
    # Collapse all other error-like statuses into Query Error
    if 'error' in text.lower() or 'unknown' in text.lower() or 'sql' in text.lower() or 'query' in text.lower():
        return 'Query Error'
    return 'Query Error'

def evaluate_from_eval_column(all_runs_file: str, output_dir: str = None, eval_column: str = 'eval_result'):
    """
    Build result_df and question_summary_df using an existing eval column without executing code.

    Returns tuple: (result_df, question_summary_df)
    """
    logger.info(f"Loading all_runs file (eval-only): {all_runs_file}")
    try:
        df = pd.read_csv(all_runs_file)
    except Exception as e:
        logger.error(f"Failed to read all_runs file: {e}")
        raise

    if eval_column not in df.columns:
        raise ValueError(f"Column '{eval_column}' not found in input CSV")

    result_df = df.copy()
    # Strictly use the provided eval_column for normalization
    result_df['comparison_result'] = result_df[eval_column].map(_normalize_eval_result_to_comparison)
    # Keep an exception column for schema parity; not applicable in eval-only
    result_df['exception'] = None

    question_summary_df = create_question_summary(result_df, comparison_col='comparison_result')

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y_%m_%d-%H_%M_%S')
        output_file = os.path.join(output_dir, f'evaluated_all_runs_{timestamp}.csv')
        result_df.to_csv(output_file, index=False)
        logger.info(f"Saved evaluated results to: {output_file}")
        question_summary_file = os.path.join(output_dir, f'question_summary_{timestamp}.csv')
        question_summary_df.to_csv(question_summary_file, index=False)
        logger.info(f"Saved question summary to: {question_summary_file}")

    return result_df, question_summary_df

## Removed evaluate_all_runs execution path; script operates in eval-only mode

def create_question_summary(df, comparison_col: str = 'comparison_result'):
    """
    Create a summary DataFrame with unique question IDs and has_match column.
    
    Args:
        df (pd.DataFrame): DataFrame with evaluation results
    
    Returns:
        pd.DataFrame: Summary DataFrame with question_id and has_match columns
    """
    # Create a unique question identifier
    df['question_id'] = df['question'].astype(str) + '_' + df['db_name'].astype(str) + '_' + df['dataset_name'].astype(str)
    
    # Group by question_id and check if any result is a match
    agg_dict = {
        'question': 'first',
        'db_name': 'first', 
        'dataset_name': 'first',
        'comparison_result': lambda x: 'Match' if 'Match' in x.values else 'No Match'
    }
    # Carry complexity/difficulty if present
    if 'complexity' in df.columns:
        agg_dict['complexity'] = 'first'
    if 'difficulty' in df.columns:
        agg_dict['difficulty'] = 'first'

    # Use provided comparison column for aggregation by temporarily aligning name
    tmp = df.copy()
    if comparison_col != 'comparison_result' and comparison_col in tmp.columns:
        tmp = tmp.rename(columns={comparison_col: 'comparison_result'})
    question_groups = tmp.groupby('question_id').agg(agg_dict).reset_index()
    
    # Create the has_match column
    question_groups['has_match'] = question_groups['comparison_result'] == 'Match'
    
    # Reorder columns for better readability
    base_cols = ['question_id', 'question', 'db_name', 'dataset_name', 'comparison_result', 'has_match']
    # Insert optional columns in a stable order if present
    if 'complexity' in question_groups.columns:
        base_cols.insert(4, 'complexity')
    if 'difficulty' in question_groups.columns:
        # After complexity if both exist, otherwise before comparison_result
        insert_pos = 5 if 'complexity' in question_groups.columns else 4
        base_cols.insert(insert_pos, 'difficulty')
    question_summary = question_groups[base_cols]
    
    return question_summary

def _parse_df_from_json(gen_df_json):
    """Parse a pandas DataFrame from a gen_df_json string; return None on failure."""
    if not isinstance(gen_df_json, str) or gen_df_json.strip().lower() in ('', 'nan', 'none'):
        return None
    try:
        data = json.loads(gen_df_json)
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            return pd.DataFrame([data])
        return None
    except Exception:
        try:
            cleaned = gen_df_json.replace('\n', '').replace('\r', '')
            data = json.loads(cleaned)
            if isinstance(data, list):
                return pd.DataFrame(data)
            if isinstance(data, dict):
                return pd.DataFrame([data])
            return None
        except Exception:
            return None




def _print_final_ensemble_results(final_winner_results_per_method: dict, section_name: str = ""):
    """Helper function to print final ensemble per-method results."""
    if not final_winner_results_per_method:
        return
    
    try:
        section_label = f" ({section_name})" if section_name else ""
        print(f"\nFINAL ENSEMBLE PER-METHOD RESULTS{section_label}:")
        for method, metrics in final_winner_results_per_method.items():
                total_q = metrics.get('total_questions', 0)
                m_cnt = metrics.get('winner_match_count', 0)
                nm_cnt = metrics.get('winner_no_match_count', 0)
                qe_cnt = metrics.get('winner_query_error_count_adjusted', 0)
                m_pct = (m_cnt / total_q * 100.0) if total_q > 0 else 0.0
                nm_pct = (nm_cnt / total_q * 100.0) if total_q > 0 else 0.0
                qe_pct = (qe_cnt / total_q * 100.0) if total_q > 0 else 0.0
                print(f"  {method}:")
                print(f"    Match: {m_cnt}/{total_q} ({m_pct:.1f}%)")
                print(f"    No Match: {nm_cnt}/{total_q} ({nm_pct:.1f}%)")
                print(f"    Query Error: {qe_cnt}/{total_q} ({qe_pct:.1f}%)")
    except Exception as e:
        section_suffix = f" ({section_name})" if section_name else ""
        print(f"\n[WARNING] Failed to print final ensemble per-method results{section_suffix}: {e}")


def print_summary(result_df,
                  question_summary_df,
                  final_winner_results_per_method: dict = None):
    """
    Print a formatted summary of the evaluation results.
    
    Args:
        result_df (pd.DataFrame): DataFrame with all evaluation results
        question_summary_df (pd.DataFrame): DataFrame with question summary
    """
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    
    # Overall statistics
    total_runs = len(result_df)
    comparison_counts = result_df['comparison_result'].value_counts()
    total_percentages = (comparison_counts / total_runs * 100).round(2)
    
    print(f"\nOVERALL RESULTS (Total runs: {total_runs}):")
    for result_type, count in comparison_counts.items():
        percentage = total_percentages[result_type]
        print(f"  {result_type}: {count} ({percentage}%)")
    
    # Question-level statistics
    total_questions = len(question_summary_df)
    questions_with_match = question_summary_df['has_match'].sum()
    questions_without_match = total_questions - questions_with_match
    
    print(f"\nQUESTION-LEVEL RESULTS (Total unique questions: {total_questions}):")
    print(f"  Questions with at least one match: {questions_with_match} ({questions_with_match/total_questions*100:.1f}%)")
    print(f"  Questions with no matches: {questions_without_match} ({questions_without_match/total_questions*100:.1f}%)")

    # Trimmed: no per-model, per-db, or tie-break sections

    # Final ensemble per-method results using winners' eval_result across all questions
    _print_final_ensemble_results(final_winner_results_per_method)

    print("\n" + "="*80)


def _log_mlflow_stats(args,
                      result_df: pd.DataFrame,
                      question_summary_df: pd.DataFrame,
                      final_winner_results_per_method: dict = None):
    """Log Overall, Question-level, and Final ensemble results into MLflow."""
    if getattr(args, 'disable_mlflow', False):
        return
    if mlflow is None:
        logger.warning("MLflow not available; skipping MLflow logging.")
        return

    try:
        def _sanitize_mlflow_name(name: str) -> str:
            # Replace disallowed '|' with ':' and any other invalid chars with '_'
            name = name.replace('|', ':')
            return re.sub(r'[^A-Za-z0-9_.:\-\/ ]', '_', name)
        # Load credentials from ~/.env if available (align with prompt_evaluation)
        if load_dotenv is not None:
            try:
                env_path = Path.home() / ".env"
                load_dotenv(dotenv_path=env_path)
                logger.info(f"Loaded MLflow credentials from {env_path}")
            except Exception:
                pass

        # Allow token override via CLI argument
        if getattr(args, 'mlflow_token', None):
            os.environ['MLFLOW_TRACKING_TOKEN'] = str(args.mlflow_token)

        # Optional setup
        if getattr(args, 'mlflow_uri', None):
            mlflow.set_tracking_uri(args.mlflow_uri)
        if getattr(args, 'mlflow_experiment', None):
            mlflow.set_experiment(args.mlflow_experiment)

        started_here = False
        if mlflow.active_run() is None:
            run_name = getattr(args, 'mlflow_run_name', None) or 'evaluate_all_runs'
            mlflow.start_run(run_name=run_name)
            started_here = True

        # Log the original all_runs CSV file as an artifact for traceability
        try:
            src_csv = getattr(args, 'all_runs', None)
            if src_csv and os.path.isfile(src_csv):
                mlflow.log_artifact(src_csv, artifact_path='inputs')
        except Exception:
            # Best-effort; continue if artifact logging fails
            pass

        # Log parameters used to call the script (masking sensitive values)
        try:
            # Log the exact command invocation
            try:
                mlflow.log_param('script_command', ' '.join(sys.argv))
            except Exception:
                pass

            # Helper to serialize values
            def _serialize_param_value(val):
                try:
                    if val is None:
                        return None
                    if isinstance(val, (list, tuple)):
                        return ','.join([str(v) for v in val])
                    if isinstance(val, dict):
                        return json.dumps(val)
                    return str(val)
                except Exception:
                    return str(val)

            for k, v in vars(args).items():
                if v is None:
                    continue
                name = _sanitize_mlflow_name(f'arg__{k}')
                lower_k = str(k).lower()
                value_to_log = _serialize_param_value(v)
                if any(s in lower_k for s in ['token', 'password', 'secret', 'key', 'credential']):
                    # Avoid leaking secrets; indicate presence without value
                    value_to_log = '***'
                try:
                    mlflow.log_param(name, value_to_log)
                except Exception:
                    # Best-effort; continue on individual failures
                    pass
        except Exception:
            # Non-fatal if parameter logging fails
            pass

        # Log any extra CLI params that were not defined in argparse but passed by the user
        try:
            extra_cli_params = getattr(args, 'extra_cli_params', None)
            if isinstance(extra_cli_params, dict) and extra_cli_params:
                for k, v in extra_cli_params.items():
                    name = _sanitize_mlflow_name(str(k))
                    lower_k = str(k).lower()
                    value_to_log = _serialize_param_value(v)
                    if any(s in lower_k for s in ['token', 'password', 'secret', 'key', 'credential']):
                        value_to_log = '***'
                    try:
                        mlflow.log_param(name, value_to_log)
                    except Exception:
                        pass
        except Exception:
            # Continue even if extra-params logging fails
            pass

        # Overall results
        total_runs = len(result_df)
        comparison_counts = result_df['comparison_result'].value_counts()
        total_percentages = (comparison_counts / total_runs * 100).round(2)
        mlflow.log_metric('overall_total_runs', int(total_runs))
        for result_type, count in comparison_counts.items():
            mlflow.log_metric(f'overall_count_{str(result_type).replace(" ", "_")}', int(count))
            pct_val = float(total_percentages[result_type]) if result_type in total_percentages else 0.0
            mlflow.log_metric(f'overall_pct_{str(result_type).replace(" ", "_")}', pct_val)

        # Question-level results
        total_questions = len(question_summary_df)
        questions_with_match = int(question_summary_df['has_match'].sum())
        questions_without_match = int(total_questions - questions_with_match)
        pct_with_match = (questions_with_match / total_questions * 100.0) if total_questions > 0 else 0.0
        pct_without_match = (questions_without_match / total_questions * 100.0) if total_questions > 0 else 0.0
        mlflow.log_metric('questions_total', int(total_questions))
        mlflow.log_metric('questions_with_match', int(questions_with_match))
        mlflow.log_metric('questions_without_match', int(questions_without_match))
        mlflow.log_metric('questions_with_match_pct', float(pct_with_match))
        mlflow.log_metric('questions_without_match_pct', float(pct_without_match))

        # Question-level breakdowns by complexity/difficulty
        try:
            if 'complexity' in question_summary_df.columns:
                comp_group = question_summary_df.groupby('complexity')['has_match'].agg(['sum', 'count']).reset_index()
                for _, row in comp_group.iterrows():
                    label = _sanitize_mlflow_name(str(row['complexity']))
                    total = int(row['count'])
                    matches = int(row['sum'])
                    pct = (matches / total * 100.0) if total > 0 else 0.0
                    mlflow.log_metric(f'questions_by_complexity__{label}__total', total)
                    mlflow.log_metric(f'questions_by_complexity__{label}__with_match', matches)
                    mlflow.log_metric(f'questions_by_complexity__{label}__with_match_pct', float(pct))
            if 'difficulty' in question_summary_df.columns:
                diff_group = question_summary_df.groupby('difficulty')['has_match'].agg(['sum', 'count']).reset_index()
                for _, row in diff_group.iterrows():
                    label = _sanitize_mlflow_name(str(row['difficulty']))
                    total = int(row['count'])
                    matches = int(row['sum'])
                    pct = (matches / total * 100.0) if total > 0 else 0.0
                    mlflow.log_metric(f'questions_by_difficulty__{label}__total', total)
                    mlflow.log_metric(f'questions_by_difficulty__{label}__with_match', matches)
                    mlflow.log_metric(f'questions_by_difficulty__{label}__with_match_pct', float(pct))
        except Exception:
            pass

        # Final ensemble per-method results
        if final_winner_results_per_method:
            for key, metrics in final_winner_results_per_method.items():
                prefix = _sanitize_mlflow_name(f'final__{key}')
                total_q = int(metrics.get('total_questions', 0))
                m_cnt = int(metrics.get('winner_match_count', 0))
                nm_cnt = int(metrics.get('winner_no_match_count', 0))
                qe_cnt = int(metrics.get('winner_query_error_count_adjusted', 0))
                m_pct = (m_cnt / total_q * 100.0) if total_q > 0 else 0.0
                nm_pct = (nm_cnt / total_q * 100.0) if total_q > 0 else 0.0
                qe_pct = (qe_cnt / total_q * 100.0) if total_q > 0 else 0.0
                mlflow.log_metric(f'{prefix}__total_questions', total_q)
                mlflow.log_metric(f'{prefix}__winner_match_count', m_cnt)
                mlflow.log_metric(f'{prefix}__winner_no_match_count', nm_cnt)
                mlflow.log_metric(f'{prefix}__winner_query_error_count', qe_cnt)
                mlflow.log_metric(f'{prefix}__winner_match_pct', float(m_pct))
                mlflow.log_metric(f'{prefix}__winner_no_match_pct', float(nm_pct))
                mlflow.log_metric(f'{prefix}__winner_query_error_pct', float(qe_pct))

        # Best_(statistic) logs using final winner results (match criterion)
        if final_winner_results_per_method:
            try:
                best_match_pct = -1.0
                per_key_percentages = {}
                for key, metrics in final_winner_results_per_method.items():
                    total_q = int(metrics.get('total_questions', 0))
                    m_cnt = int(metrics.get('winner_match_count', 0))
                    nm_cnt = int(metrics.get('winner_no_match_count', 0))
                    qe_cnt = int(metrics.get('winner_query_error_count_adjusted', 0))
                    if total_q > 0:
                        match_pct = (m_cnt / total_q) * 100.0
                        no_match_pct = (nm_cnt / total_q) * 100.0
                        query_error_pct = (qe_cnt / total_q) * 100.0
                    else:
                        match_pct = 0.0
                        no_match_pct = 0.0
                        query_error_pct = 0.0
                    per_key_percentages[key] = (match_pct, no_match_pct, query_error_pct)
                    if match_pct > best_match_pct:
                        best_match_pct = match_pct

                # Collect all keys tied for best match percentage
                if per_key_percentages:
                    tolerance = 1e-9
                    best_keys = [k for k, (mp, _, _) in per_key_percentages.items() if abs(mp - best_match_pct) <= tolerance]
                    if len(best_keys) > 0:
                        sanitized_keys = [_sanitize_mlflow_name(str(k)) for k in best_keys]
                        mlflow.log_param('Best_Ensemble_Pairing', ','.join(sanitized_keys))
                        # Log best percentages; match pct is identical across ties
                        mlflow.log_metric('Best_Match', float(best_match_pct))
                        # For No Match / Query Error, use the first best key for backward-compat
                        first_key = best_keys[0]
                        _, nm_pct, qe_pct = per_key_percentages[first_key]
                    mlflow.log_metric('Best_No_Match', float(nm_pct))
                    mlflow.log_metric('Best_Query_Error', float(qe_pct))
            except Exception:
                # Non-fatal; continue without best-of logs
                pass

        if started_here:
            mlflow.end_run()
    except Exception as e:
        logger.warning(f"Failed to log MLflow metrics: {e}")

def main():
    """Main function to run the evaluation script."""
    parser = argparse.ArgumentParser(
        description="Evaluate all_runs files using test_data.eval functions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python evaluate_all_runs.py --all-runs results/all_model_runs.csv --db-base-path /path/to/dbs --metadata-base-path /path/to/metadata
  python evaluate_all_runs.py --all-runs results/all_model_runs.csv --db-base-path /path/to/dbs --metadata-base-path /path/to/metadata --output-dir ./evaluation_results
        """
    )
    
    parser.add_argument(
        '--all-runs',
        required=True,
        help='Path to the all_runs CSV file'
    )
    
    parser.add_argument(
        '--output-dir',
        help='Directory to save output files (optional)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--ensemble-selection-method', '--ensemble_selection_method',
        choices=['size', 'frequency', 'random', 'density', 'agent_indiv_grade', 'binary_comp_selection', 'double_elim', 'reverse_size', 'reverse_frequency', 'reverse_density'],
        default='size',
        help='[DEPRECATED] Use --ensemble-methods instead to specify one or more methods'
    )
    parser.add_argument(
        '--ensemble-methods', '--ensemble_methods',
        nargs='*',
        help='List of ensemble selection methods to run and summarize (e.g., size frequency density or "size,frequency,density")'
    )
    parser.add_argument(
        '--tie-breakers', '--tie_breakers',
        nargs='*',
        help='List of tie-breaker methods to run for finalists (random, density, size). Default: random'
    )
    parser.add_argument(
        '--eval-column', '--eval_column',
        default='eval_result',
        help='Name of the column to use when --use-eval-result-only is enabled (default: eval_result)'
    )
    parser.add_argument(
        '--eval-type', '--eval_type',
        choices=['custom', 'bird'],
        default='custom',
        help='Select which eval column to use from CSV: custom uses eval_custom; bird uses eval_bird'
    )

    # MLflow options
    parser.add_argument(
        '--mlflow-uri', '--mlflow_uri',
        help='Override MLflow tracking URI (e.g., file:./mlruns)'
    )
    parser.add_argument(
        '--mlflow-experiment', '--mlflow_experiment',
        help='MLflow experiment name to log metrics under'
    )
    parser.add_argument(
        '--mlflow-run-name', '--mlflow_run_name',
        help='MLflow run name to use when starting a run'
    )
    parser.add_argument(
        '--mlflow-token', '--mlflow_token',
        help='MLflow tracking token to authenticate API requests'
    )
    parser.add_argument(
        '--disable-mlflow', '--disable_mlflow',
        action='store_true',
        help='Skip MLflow logging'
    )
    
    # Parse known args, capturing any unknown flags for MLflow logging
    args, _unknown_cli_tokens = parser.parse_known_args()
    # Re-parse from sys.argv to retain exact token order for unknowns
    try:
        argv_tokens = sys.argv[1:]
    except Exception:
        argv_tokens = []
    extra_cli_params = {}
    try:
        idx = 0
        while idx < len(argv_tokens):
            token = argv_tokens[idx]
            if isinstance(token, str) and token.startswith('--'):
                raw = token[2:]
                # Skip if this flag is defined in argparse schema
                defined = any(raw == a or raw.replace('-', '_') == a.replace('-', '_') for a in vars(args).keys())
                if defined:
                    # If this known flag takes a value, skip its value too
                    # Heuristic: if next token exists and doesn't start with '-', assume it's a value
                    if (idx + 1) < len(argv_tokens) and not str(argv_tokens[idx + 1]).startswith('-'):
                        idx += 1
                else:
                    if '=' in raw:
                        key, val = raw.split('=', 1)
                        extra_cli_params[key] = val
                    else:
                        # Lookahead for value
                        if (idx + 1) < len(argv_tokens) and not str(argv_tokens[idx + 1]).startswith('-'):
                            extra_cli_params[raw] = argv_tokens[idx + 1]
                            idx += 1
                        else:
                            extra_cli_params[raw] = True
            idx += 1
    except Exception:
        # Best-effort; ignore failures
        pass
    # Attach for downstream MLflow logging
    setattr(args, 'extra_cli_params', extra_cli_params)
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    if not os.path.exists(args.all_runs):
        logger.error(f"All runs file not found: {args.all_runs}")
        sys.exit(1)
    
    try:
        # Always run in eval-only mode using the selected eval type
        eval_column = 'eval_custom' if str(getattr(args, 'eval_type', 'custom')).lower() == 'custom' else 'eval_bird'
        # If user explicitly passed --eval-column, allow override (back-compat)
        try:
            argv_tokens = sys.argv[1:]
        except Exception:
            argv_tokens = []
        user_overrode_eval_col = any(t in argv_tokens for t in ['--eval-column', '--eval_column'])
        if user_overrode_eval_col:
            eval_column = args.eval_column
        logger.info(f"Starting evaluation (no code execution). Using column: {eval_column}")
        result_df, question_summary_df = evaluate_from_eval_column(
            args.all_runs,
            args.output_dir,
            eval_column=eval_column,
        )

        # Normalize grouping keys: ensure 'question_index' exists using 'index' if present
        try:
            if 'question_index' not in result_df.columns:
                if 'index' in result_df.columns:
                    result_df['question_index'] = result_df['index']
            else:
                if 'index' in result_df.columns:
                    result_df['question_index'] = result_df['question_index'].where(
                        result_df['question_index'].notna(), result_df['index']
                    )
        except Exception:
            # Best-effort normalization; continue if mapping fails
            pass

        # Filter to valid candidates for ensembling: non-empty, JSON-parsable gen_df_json
        def _is_valid_gen_df_json(val):
            try:
                if not isinstance(val, str):
                    return False
                text = val.strip()
                if text == '' or text.lower() in ('nan', 'none', 'null'):
                    return False
                try:
                    json.loads(text)
                    return True
                except Exception:
                    cleaned = text.replace('\n', '').replace('\r', '')
                    json.loads(cleaned)
                    return True
            except Exception:
                return False

        try:
            df_valid = result_df[result_df['gen_df_json'].apply(_is_valid_gen_df_json)].copy()
        except Exception:
            df_valid = result_df.copy()

        # Optional: compute ensemble winners per requested methods and evaluate Match/No Match percentages
        # Determine which ensemble methods to run; prefer --ensemble-methods, fallback to deprecated flag
        def _normalize_methods(methods_raw):
            allowed = ['size', 'frequency', 'random', 'density', 'agent_indiv_grade', 'binary_comp_selection', 'double_elim', 'reverse_size', 'reverse_frequency', 'reverse_density']
            if not methods_raw:
                return []
            # Flatten and split on commas; lowercase and strip
            tokens = []
            for item in methods_raw:
                if isinstance(item, str):
                    parts = [p.strip().lower() for p in item.replace(';', ',').split(',') if p.strip()]
                    if parts:
                        tokens.extend(parts)
                else:
                    try:
                        tokens.append(str(item).strip().lower())
                    except Exception:
                        pass
            # Filter to allowed and de-duplicate preserving order
            seen = set()
            normalized = []
            for t in tokens:
                if t in allowed and t not in seen:
                    seen.add(t)
                    normalized.append(t)
                elif t not in allowed:
                    logger.warning(f"Skipping unknown ensemble method: {t}")
            return normalized

        methods_to_use = _normalize_methods(args.ensemble_methods) if args.ensemble_methods and len(args.ensemble_methods) > 0 else _normalize_methods([args.ensemble_selection_method])
        def _normalize_tie_breakers(tb_raw):
            allowed_tb = ['random', 'density', 'size']
            if not tb_raw:
                return ['random']
            tokens = []
            for item in tb_raw:
                if isinstance(item, str):
                    parts = [p.strip().lower() for p in item.replace(';', ',').split(',') if p.strip()]
                    if parts:
                        tokens.extend(parts)
                else:
                    try:
                        tokens.append(str(item).strip().lower())
                    except Exception:
                        pass
            seen = set()
            normalized = []
            for t in tokens:
                if t in allowed_tb and t not in seen:
                    seen.add(t)
                    normalized.append(t)
                elif t not in allowed_tb:
                    logger.warning(f"Skipping unknown tie-breaker: {t}")
            return normalized if normalized else ['random']

        tie_breakers_to_use = _normalize_tie_breakers(args.tie_breakers)
        if methods_to_use:
            logger.info(f"Ensemble methods selected: {methods_to_use}")
        else:
            logger.info("No valid ensemble methods provided; skipping ensemble comparison.")


        # Trimmed: skip tie-break/finalist stats per method

        # Execute ensemble functions for each requested method|tie-breaker to obtain actual winners
        winners_per_method = {}
        for method in methods_to_use:
            for tb in tie_breakers_to_use:
                key = f"{method}|tb:{tb}"
                try:
                    winners_df_exec = ensemble_from_all_runs_df(
                        df_valid,
                        ensemble_selection_method=method,
                        use_gradio_agent=False,
                        mlflow_run_id=None,
                        tie_break_method=tb,
                    )
                    winners_per_method[key] = winners_df_exec
                except Exception as e:
                    logger.warning(f"Failed executing ensemble method {method} with tie-breaker {tb}: {e}")

        # Build final per-method winner outcome results using executed winners (LLM may be called)
        final_winner_results_per_method = {}
        try:
            for key, winners_df_exec in winners_per_method.items():
                # Merge winners with a single aggregated label per (question, db, dataset, question_index, model_name)
                merge_keys = ['question', 'dataset_name', 'db_name', 'question_index', 'model_name']
                for k in merge_keys:
                    if k not in winners_df_exec.columns:
                        raise KeyError(f"Winners DF missing key column: {k}")

                # One winner per question
                winners_unique = winners_df_exec.drop_duplicates(subset=['question', 'dataset_name', 'db_name', 'question_index'])

                # Build aggregated labels to avoid duplicate inflation on merge
                labels = result_df.copy()
                norm = labels['comparison_result'].astype(str).str.strip()
                norm = norm.where(norm.isin(['Match', 'No Match']), other='Query Error')
                labels['comparison_result_norm'] = norm

                def _reduce_labels(series):
                    vals = set(str(v).strip() for v in series if pd.notna(v))
                    if 'Match' in vals:
                        return 'Match'
                    if 'No Match' in vals:
                        return 'No Match'
                    return 'Query Error'

                agg_labels = labels.groupby(merge_keys)['comparison_result_norm'].agg(_reduce_labels).reset_index().rename(columns={'comparison_result_norm': 'winner_label'})

                merged = winners_unique.merge(agg_labels, on=merge_keys, how='left')

                # Denominator: total unique questions
                total_questions = int(question_summary_df.shape[0]) if 'question_summary_df' in locals() and question_summary_df is not None else int(result_df.assign(question_id=result_df['question'].astype(str) + '_' + result_df['db_name'].astype(str) + '_' + result_df['dataset_name'].astype(str))['question_id'].nunique())

                # Count only the single winner per question; missing labels => Query Error
                winner_label = merged['winner_label'].astype(str).str.strip().fillna('Query Error')
                winner_label = winner_label.where(winner_label.isin(['Match', 'No Match']), other='Query Error')
                winner_match_count = int((winner_label == 'Match').sum())
                winner_no_match_count = int((winner_label == 'No Match').sum())
                accounted = winner_match_count + winner_no_match_count
                winner_query_error_count = max(0, total_questions - accounted)
                final_winner_results_per_method[key] = {
                    'total_questions': int(total_questions),
                    'winner_match_count': winner_match_count,
                    'winner_no_match_count': winner_no_match_count,
                    'winner_query_error_count_adjusted': winner_query_error_count,
                }
        except Exception as e:
            logger.warning(f"Failed building executed final winner results: {e}")

        # Print summary
        print_summary(
            result_df,
            question_summary_df,
            final_winner_results_per_method=final_winner_results_per_method,
        )

        # Log stats to MLflow
        _log_mlflow_stats(
            args,
            result_df,
            question_summary_df,
            final_winner_results_per_method=final_winner_results_per_method,
        )
        
        logger.info("Evaluation completed successfully!")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
