"""Generate a validated full-Registry revision plan from human feedback."""

from src.deepseek_client import encoded

from .prompt_loader import stage_messages
from .validator import validate_registry_revision_plan


def run_registry_revision(human_feedback, existing_registry, llm_client,
                          prompt_loader, *, batch_name='registry_revision',
                          prompt_version=None, return_call_record=False):
    """Call the revision LLM for the complete current Registry."""
    prompts = (prompt_loader.get_active_prompts()
               if hasattr(prompt_loader, 'get_active_prompts')
               else prompt_loader)
    version = prompt_version or getattr(prompt_loader, 'current_version', None)
    if not version:
        raise ValueError('Registry Revision 缺少 Prompt 版本')
    system, user = stage_messages(prompts, 'registry_revision', {
        'human_feedback': human_feedback,
        'existing_registry': encoded(existing_registry),
    })
    revision_plan, call_record = llm_client.call(
        stage='registry_revision', window_name=batch_name,
        prompt_version=version, system=system, user=user,
        validator=lambda value: validate_registry_revision_plan(
            value, existing_registry))
    if return_call_record:
        return revision_plan, call_record
    return revision_plan
