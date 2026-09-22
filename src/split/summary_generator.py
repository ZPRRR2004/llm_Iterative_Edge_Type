"""Generate validated one-sentence previous and future trajectory summaries."""
import json
import re
from pathlib import Path

from src.deepseek_client import Client

from .token_counter import count_text_tokens, serialize_events


class SummaryError(RuntimeError):
    pass


class SummaryGenerator:
    def __init__(self, working_directory, *, model='deepseek-flash',
                 base_url='https://api.deepseek.com', prompts_directory=None,
                 retries=2, transport=None):
        self.prompts_directory = (Path(prompts_directory) if prompts_directory else
                                  Path(__file__).resolve().parent / 'prompts')
        self.retries = retries
        self.client = Client(working_directory, model=model, base_url=base_url,
                             retries=3, transport=transport)

    def _prompt(self, kind, name):
        path = self.prompts_directory / kind / f'{name}.txt'
        return path.read_text(encoding='utf-8').strip()

    @staticmethod
    def _user_query(user_query):
        return json.dumps({'title': user_query['title'], 'text': user_query['text']},
                          ensure_ascii=False, indent=2)

    def _render_user(self, kind, user_query, events, max_tokens):
        values = {
            'user_query': self._user_query(user_query),
            f'{kind}_trajectory': serialize_events(events),
            f'max_{kind}_summary_tokens': str(max_tokens),
        }
        rendered = self._prompt(kind, 'user')
        for key, value in values.items():
            rendered = rendered.replace('{{' + key + '}}', value)
        unresolved = re.findall(r'{{[^{}]+}}', rendered)
        if unresolved:
            raise SummaryError(f'Unresolved prompt placeholders: {unresolved}')
        return rendered

    def _render_retry(self, validation_error, previous_response):
        values = {
            'validation_error': validation_error,
            'previous_response': previous_response,
        }
        template = (self.prompts_directory / 'retry.txt').read_text(
            encoding='utf-8').strip()

        def substitute(match):
            key = match.group(1)
            if key not in values:
                raise SummaryError(f'Unknown retry prompt placeholder: {key}')
            return values[key]

        return re.sub(r'{{([a-z_]+)}}', substitute, template)

    @staticmethod
    def _validate_summary(summary, max_tokens):
        summary = summary.strip()
        if not summary:
            raise SummaryError('Summary is empty')
        if '\n' in summary or '\r' in summary:
            raise SummaryError('Summary must be one line')
        if re.match(r'^(?:[-*#]|\d+[.)])\s+', summary):
            raise SummaryError('Summary must be one sentence without list formatting')
        estimated = count_text_tokens(summary)
        if estimated > max_tokens:
            raise SummaryError(
                f'Summary estimate {estimated} exceeds configured limit {max_tokens}')
        return summary

    def _generate(self, kind, user_query, events, max_tokens):
        if not events or max_tokens == 0:
            return ''

        system = self._prompt(kind, 'system')
        base_user = self._render_user(kind, user_query, events, max_tokens)
        error = None
        previous_response = ''
        for attempt in range(self.retries + 1):
            user = base_user
            if error is not None:
                user += '\n\n' + self._render_retry(error, previous_response)
            messages = self.client.redactor.walk([
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ])
            payload = {
                'model': self.client.model,
                'messages': messages,
                'max_tokens': max_tokens,
                'thinking': {'type': 'disabled'},
                'temperature': 0,
                'stream': False,
            }
            raw = self.client.transport(payload)
            try:
                choice = raw['choices'][0]
                content = choice['message'].get('content') or ''
                previous_response = self.client.redactor.walk(content, restore=True)
                if choice.get('finish_reason') != 'stop':
                    raise SummaryError(
                        f'incomplete response: finish_reason={choice.get("finish_reason")}')
                return self._validate_summary(previous_response, max_tokens)
            except (KeyError, IndexError, TypeError, SummaryError) as exc:
                error = str(exc)

        raise SummaryError(
            f'{kind} summary failed after {self.retries + 1} attempts: {error}')

    def previous(self, user_query, events, max_tokens):
        return self._generate('previous', user_query, events, max_tokens)

    def future(self, user_query, events, max_tokens):
        return self._generate('future', user_query, events, max_tokens)
