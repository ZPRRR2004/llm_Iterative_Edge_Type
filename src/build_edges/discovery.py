"""Step 1: blind edge type discovery."""

from .prompt_loader import stage_messages
from .validator import validate_discovery


def run_discovery(*, context_window, llm_client, prompts,
                  window_name, prompt_version):
    system, user = stage_messages(
        prompts, 'discovery', {'context_window': context_window})
    return llm_client.call(
        stage='discovery', window_name=window_name,
        prompt_version=prompt_version, system=system, user=user,
        validator=validate_discovery)
