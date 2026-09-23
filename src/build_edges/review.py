"""Step 3: review new candidates and revise matched Registry types."""

from src.deepseek_client import encoded

from .prompt_loader import stage_messages
from .validator import validate_review


def run_review(*, context_window, candidate_types, comparison_result,
               existing_registry, llm_client, prompts,
               window_name, prompt_version):
    system, user = stage_messages(prompts, 'review', {
        'context_window': context_window,
        'candidate_edge_types': encoded(candidate_types),
        'comparison_results': encoded(comparison_result),
        'existing_registry': encoded(existing_registry),
    })
    return llm_client.call(
        stage='review', window_name=window_name,
        prompt_version=prompt_version, system=system, user=user,
        validator=lambda value: validate_review(
            value, candidate_types, comparison_result, existing_registry))
