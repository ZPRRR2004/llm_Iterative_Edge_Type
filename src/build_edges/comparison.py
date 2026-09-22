"""Step 2: compare candidates against the current Registry snapshot."""

from src.deepseek_client import encoded

from .prompt_loader import stage_messages
from .validator import validate_comparison


def run_comparison(*, candidate_types, existing_registry, llm_client,
                   prompts, window_name, prompt_version):
    system, user = stage_messages(prompts, 'comparison', {
        'candidate_edge_types': encoded(candidate_types),
        'existing_registry': encoded(existing_registry),
    })
    return llm_client.call(
        stage='comparison', window_name=window_name,
        prompt_version=prompt_version, system=system, user=user,
        validator=lambda value: validate_comparison(
            value, candidate_types, existing_registry))
