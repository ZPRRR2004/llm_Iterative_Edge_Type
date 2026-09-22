"""Validated JSON LLM calls with stage retries and auditable records."""
import time
from datetime import datetime, timezone

from src.deepseek_client import Client, encoded, strict_json


STAGE_LABELS = {
    'discovery': 'Step 1 - Blind Discovery',
    'comparison': 'Step 2 - Type Comparison',
    'review': 'Step 3 - Type Review',
    'registry_revision': 'Registry Revision',
}


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


class StageCallError(RuntimeError):
    def __init__(self, message, record):
        super().__init__(message)
        self.record = record


class BuildEdgesLLM:
    def __init__(self, output_dir, *, model='deepseek-flash',
                 base_url='https://api.deepseek.com', max_retries=3,
                 max_tokens=32768, context_tokens=1048576,
                 timeout=600, transport=None):
        if not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries < 0:
            raise ValueError('max_retries 必须是非负整数')
        self.max_retries = max_retries
        # Stage-level retry is authoritative; disable the shared client's nested HTTP retry.
        self.client = Client(output_dir, model=model, base_url=base_url,
                             max_tokens=max_tokens, context_tokens=context_tokens,
                             timeout=timeout, retries=0, transport=transport)

    @property
    def model(self):
        return self.client.model

    def call(self, *, stage, window_name, prompt_version,
             system, user, validator):
        safe_system = self.client.redactor.walk(
            system, location=f'{window_name}.{stage}.system')
        safe_user = self.client.redactor.walk(
            user, location=f'{window_name}.{stage}.user')
        messages = [
            {'role': 'system', 'content': safe_system},
            {'role': 'user', 'content': safe_user},
        ]
        payload = {
            'model': self.client.model,
            'messages': messages,
            'response_format': {'type': 'json_object'},
            'max_tokens': self.client.max_tokens,
            'thinking': {'type': 'enabled'},
            'reasoning_effort': 'high',
            'stream': False,
        }
        started_at = _utc_now()
        started = time.monotonic()
        estimate = (len(encoded(messages).encode('utf-8')) + 1024 +
                    self.client.max_tokens)
        if estimate > self.client.context_tokens:
            error = (
                f'完整请求的保守容量估计 {estimate} 超过 '
                f'{self.client.context_tokens}；停止且不截断输入')
            attempts = [{
                'attempt': 1,
                'started_at': _utc_now(),
                'duration_seconds': 0,
                'raw_response': None,
                'response_content': '',
                'error': error,
            }]
            record = self._record(
                stage, prompt_version, messages, started_at, started,
                attempts, False, None)
            raise StageCallError(error, record)

        attempts = []
        parsed = None
        for attempt_index in range(self.max_retries + 1):
            attempt_started = time.monotonic()
            raw = None
            content = ''
            error = None
            try:
                raw = self.client.transport(payload)
                choice = raw['choices'][0]
                content = choice['message'].get('content') or ''
                if choice.get('finish_reason') != 'stop':
                    raise ValueError(
                        f'模型响应未完整结束：finish_reason={choice.get("finish_reason")}')
                parsed = strict_json(content)
                parsed = self.client.redactor.walk(parsed, restore=True)
                validator(parsed)
            except Exception as exc:
                error = str(exc)

            attempts.append({
                'attempt': attempt_index + 1,
                'started_at': _utc_now(),
                'duration_seconds': round(time.monotonic() - attempt_started, 6),
                'raw_response': self.client.redactor.walk(raw) if raw is not None else None,
                'response_content': self.client.redactor.walk(content),
                'error': error,
            })
            if error is None:
                record = self._record(
                    stage, prompt_version, messages, started_at, started,
                    attempts, True, parsed)
                return parsed, record

            heading = ('Registry Revision 失败'
                       if stage == 'registry_revision' else 'LLM 调用失败')
            print(f'\n【{heading}】')
            print(f'当前 Window：{window_name}')
            print(f'当前阶段：{STAGE_LABELS.get(stage, stage)}')
            print(f'失败原因：{error}')
            if attempt_index < self.max_retries:
                print(f'正在进行第 {attempt_index + 1} / {self.max_retries} 次重试...')

        record = self._record(
            stage, prompt_version, messages, started_at, started,
            attempts, False, None)
        raise StageCallError(
            f'{window_name} 的 {STAGE_LABELS.get(stage, stage)} '
            f'在 {self.max_retries} 次重试后仍失败', record)

    def _record(self, stage, prompt_version, messages, started_at,
                started, attempts, succeeded, parsed):
        return {
            'stage': stage,
            'prompt_version': prompt_version,
            'model': self.client.model,
            'started_at': started_at,
            'completed_at': _utc_now(),
            'duration_seconds': round(time.monotonic() - started, 6),
            'request': {
                'system_message': messages[0]['content'],
                'user_message': messages[1]['content'],
                'settings': {
                    'max_tokens': self.client.max_tokens,
                    'thinking': 'enabled',
                    'reasoning_effort': 'high',
                    'response_format': 'json_object',
                },
            },
            'attempts': attempts,
            'succeeded': succeeded,
            'parsed_response': parsed,
        }
