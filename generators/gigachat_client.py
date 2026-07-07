import re
import threading
import time
import uuid
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_BASE = "https://gigachat.devices.sberbank.ru/api/v1"


class GigaChatAuthError(Exception):
    pass


class GigaChatError(Exception):
    pass


class GigaChatManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def _ensure_initialized(self):
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            from config import (
                gigachat_credentials,
                gigachat_model,
                gigachat_scope,
                gigachat_token_refresh_minutes,
            )

            self.credentials = gigachat_credentials
            self.scope = gigachat_scope
            self.model = gigachat_model
            self._refresh_interval = gigachat_token_refresh_minutes * 60
            self.access_token = None
            self.expires_at = 0
            self._fetch_token()
            self._schedule_refresh()
            self._initialized = True

    def _fetch_token(self):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {self.credentials}",
        }
        response = requests.post(
            OAUTH_URL,
            headers=headers,
            data={"scope": self.scope},
            verify=False,
            timeout=30,
        )
        if response.status_code != 200:
            raise GigaChatAuthError(
                f"Не удалось получить токен GigaChat: {response.status_code} {response.text}"
            )

        data = response.json()
        self.access_token = data["access_token"]
        expires_at = data.get("expires_at")
        self.expires_at = expires_at / 1000 if expires_at else time.time() + 1800

    def _schedule_refresh(self):
        timer = threading.Timer(self._refresh_interval, self._auto_refresh)
        timer.daemon = True
        timer.start()

    def _auto_refresh(self):
        try:
            with self._lock:
                self._fetch_token()
        except Exception:
            pass
        finally:
            self._schedule_refresh()

    def get_access_token(self):
        self._ensure_initialized()
        if time.time() >= self.expires_at - 60:
            with self._lock:
                if time.time() >= self.expires_at - 60:
                    self._fetch_token()
        return self.access_token

    def _api_headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.get_access_token()}",
        }

    def chat_completion(self, system_prompt, user_prompt, function_call=None, retry=True):
        self._ensure_initialized()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        if function_call:
            payload["function_call"] = function_call

        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers=self._api_headers(),
            json=payload,
            verify=False,
            timeout=120,
        )

        if response.status_code == 401 and retry:
            with self._lock:
                self._fetch_token()
            return self.chat_completion(
                system_prompt, user_prompt, function_call, retry=False
            )

        if response.status_code != 200:
            raise GigaChatError(
                f"GigaChat API: {response.status_code} {response.text}"
            )

        return response.json()["choices"][0]["message"]["content"]

    def download_image(self, file_id):
        self._ensure_initialized()
        response = requests.get(
            f"{API_BASE}/files/{file_id}/content",
            headers={"Authorization": f"Bearer {self.get_access_token()}"},
            verify=False,
            timeout=60,
        )
        if response.status_code != 200:
            raise GigaChatError(
                f"Не удалось скачать изображение: {response.status_code}"
            )
        return response.content


def get_gigachat_manager():
    return GigaChatManager()


def chat_completion(system_prompt, user_prompt):
    return get_gigachat_manager().chat_completion(system_prompt, user_prompt)


def generate_image_file(prompt):
    content = get_gigachat_manager().chat_completion(
        "Ты генерируешь изображения для соцсетей.",
        f"Нарисуй изображение для соцсетей: {prompt}",
        function_call="auto",
    )

    file_id = _extract_file_id(content)
    if not file_id:
        raise GigaChatError(
            f"GigaChat не вернул идентификатор изображения. Ответ: {content[:200]}"
        )

    image_bytes = get_gigachat_manager().download_image(file_id)
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "static" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.jpg"
    file_path = output_dir / filename
    file_path.write_bytes(image_bytes)
    return f"/static/generated/{filename}"


def _extract_file_id(content):
    match = re.search(
        r"(?:src|href)=[\"']?"
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
        content,
        re.IGNORECASE,
    )
    if match:
        return match.group(1)

    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        content,
        re.IGNORECASE,
    )
    return match.group(0) if match else None
