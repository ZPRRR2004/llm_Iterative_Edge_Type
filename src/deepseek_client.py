"""Shared standard-library DeepSeek transport and validated response cache."""
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path



class Invalid(ValueError):
    pass


def strict_json(text):
    """Parse JSON while rejecting duplicate keys and non-finite constants."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Invalid(f'Duplicate JSON key: {key}')
            result[key] = value
        return result

    def constant(value):
        raise Invalid(f'Invalid JSON constant: {value}')

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(encoded(value) + '\n', encoding='utf-8')
    temporary.replace(path)


def prompt(name):
    path = Path(__file__).resolve().parent / 'preprocess' / 'prompts' / (name + '.md')
    return path.read_text(encoding='utf-8').strip()


def render(name, **data):
    # Substitute only original placeholders; never interpret braces inside data.
    return re.sub(r'\{([a-z_]+)\}', lambda m: encoded(data[m[1]]), prompt(name))


class InvalidResponse(RuntimeError):
    pass


class CapacityError(RuntimeError):
    pass


class Redactor:
    patterns = [
        re.compile(r'sk-[A-Za-z0-9_-]{16,}'),
        re.compile(r'(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}'),
        re.compile(r'AKIA[A-Z0-9]{16}'),
        re.compile(r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----', re.S),
        re.compile(r'(?i)(?:bearer\s+)[A-Za-z0-9._~+/-]{16,}'),
        re.compile(r'''(?i)(?:api[_-]?key|password|secret|access_token)\s*[=:]\s*["']?([^\s"',;}]{8,})'''),
    ]

    def __init__(self):
        self.originals = {}
        self.paths = set()

    def hide(self, text, location='input'):
        # Also protect the configured credential if it happens to occur in data.
        key = os.environ.get('DEEPSEEK_API_KEY')
        patterns = ([re.compile(re.escape(key))] if key else []) + self.patterns
        for pattern in patterns:
            def replace(match):
                value = match.group(0)
                token = '<REDACTED_' + hashlib.sha256(value.encode()).hexdigest()[:20] + '>'
                self.originals[token] = value
                self.paths.add(location)
                return token
            text = pattern.sub(replace, text)
        return text

    def walk(self, value, restore=False, location='input'):
        if isinstance(value, str):
            if restore:
                return re.sub(r'<REDACTED_[a-f0-9]{20}>', lambda m: self.originals.get(m[0], m[0]), value)
            return self.hide(value, location)
        if isinstance(value, list):
            return [self.walk(v, restore, f'{location}[{i}]') for i, v in enumerate(value)]
        if isinstance(value, dict):
            return {k: self.walk(v, restore, f'{location}.{k}') for k, v in value.items()}
        return value


class Client:
    def __init__(self, directory, *, model='deepseek-flash', base_url='https://api.deepseek.com',
                 max_tokens=32768, context_tokens=1048576, timeout=600,
                 retries=3, resume=False, transport=None):
        self.directory = Path(directory)
        self.model, self.base_url = model, base_url.rstrip('/')
        self.max_tokens, self.context_tokens = max_tokens, context_tokens
        self.timeout, self.retries, self.resume = timeout, retries, resume
        self.transport = transport or self.http
        self.redactor = Redactor()

    def http(self, payload):
        key = os.environ.get('DEEPSEEK_API_KEY')
        if not key:
            raise RuntimeError('请设置 DEEPSEEK_API_KEY 环境变量')
        request = urllib.request.Request(self.base_url + '/chat/completions',
            data=encoded(payload).encode(), method='POST', headers={
                'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return strict_json(response.read().decode())
            except urllib.error.HTTPError as error:
                # Avoid logging a provider response that may echo credentials.
                if error.code in (408, 429, 500, 502, 503, 504) and attempt < self.retries:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                raise RuntimeError(f'DeepSeek HTTP {error.code}; 请求未裁剪。400 时请检查模型、参数和上下文容量') from None
            except (urllib.error.URLError, TimeoutError):
                if attempt < self.retries:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                raise RuntimeError('DeepSeek 网络请求失败或超时；重新运行原命令即可继续') from None

    def ask(self, name, system_parts, user_template, data, validator, output_tokens=None,
            thinking=True, retries=None):
        system = '\n\n'.join(prompt(p) for p in ['common'] + system_parts)
        safe_data = self.redactor.walk(data)
        user = render(user_template, **safe_data)
        request_tokens = output_tokens or self.max_tokens
        validation_retries = self.retries if retries is None else retries
        if validation_retries < 0:
            raise ValueError('retries must not be negative')
        settings = {'model': self.model, 'base_url': self.base_url, 'max_tokens': request_tokens,
                    'context_tokens': self.context_tokens, 'thinking': thinking,
                    'validation_retries': validation_retries}
        digest = hashlib.sha256(encoded([system, user, settings, data]).encode()).hexdigest()
        cache = self.directory / 'cache' / (digest + '.json')
        if self.resume and cache.exists():
            answer = self.redactor.walk(strict_json(cache.read_text()), restore=True)
            validator(answer)
            print(f'[{name}] 使用已验证缓存', flush=True)
            return answer
        previous, errors = '', []
        attempt_tokens = request_tokens
        for attempt in range(validation_retries + 1):
            if attempt and errors == ['Response incomplete: finish_reason=length']:
                attempt_tokens = min(attempt_tokens * 2, self.max_tokens)
            actual_user = user
            if attempt:
                actual_user += '\n\n' + render('retry', previous_response_json=previous,
                                                validation_errors_json=errors)
            payload = {'model': self.model, 'messages': [
                {'role': 'system', 'content': system}, {'role': 'user', 'content': actual_user}],
                'response_format': {'type': 'json_object'}, 'max_tokens': attempt_tokens,
                'thinking': {'type': 'enabled' if thinking else 'disabled'}, 'stream': False}
            if thinking:
                payload['reasoning_effort'] = 'high'
            else:
                payload['temperature'] = 0
            # UTF-8 bytes are a conservative bound, not an exact tokenizer count.
            estimate = len(encoded(payload['messages']).encode()) + 1024 + attempt_tokens
            if estimate > self.context_tokens:
                raise CapacityError(f'完整请求的保守容量估计 {estimate} 超过 {self.context_tokens}；停止且不截断输入')
            print(f'[{name}] 请求 {attempt + 1}', flush=True)
            raw = self.transport(payload)
            previous = ''
            try:
                choice = raw['choices'][0]
                previous = choice['message'].get('content') or ''
                if choice.get('finish_reason') != 'stop':
                    raise Invalid('Response incomplete: finish_reason=' + str(choice.get('finish_reason')))
                answer = self.redactor.walk(strict_json(previous), restore=True)
                validator(answer)
                errors = []
            except (Invalid, ValueError, TypeError, KeyError, IndexError, RecursionError) as error:
                errors = [str(error)]
            log = {'call': name, 'attempt': attempt + 1, 'request': payload,
                   'response': previous, 'usage': raw.get('usage'), 'validation_errors': errors,
                   'redacted_fields': sorted(self.redactor.paths)}
            self.directory.mkdir(parents=True, exist_ok=True)
            log_name = 'preprocess_calls.jsonl' if name.startswith(('root', 'split')) else 'execution_calls.jsonl'
            with (self.directory / log_name).open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(self.redactor.walk(log), ensure_ascii=False) + '\n')
            if not errors:
                print(f'[{name}] 通过', flush=True)
                save(cache, self.redactor.walk(answer))
                return answer
            print(f'[{name}] 校验失败：{errors[0]}', flush=True)
        raise InvalidResponse(
            f'{name}: 共请求 {validation_retries + 1} 次后仍未通过校验: {errors[0]}')
