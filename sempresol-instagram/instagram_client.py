"""
instagram_client.py
Client per a la Instagram API amb Instagram Login (graph.instagram.com).
Publica fotos i renova el token de llarga durada.
"""

import os
import time
import requests

GRAPH = "https://graph.instagram.com/v21.0"
GRAPH_ROOT = "https://graph.instagram.com"


class InstagramClient:
    def __init__(self, access_token: str | None = None, user_id: str | None = None):
        self.access_token = access_token or os.environ["IG_ACCESS_TOKEN"]
        self.user_id = user_id or os.environ["IG_USER_ID"]
        self.session = requests.Session()

    # ── Publicació ────────────────────────────────────────────────────────────

    def _create_container(self, image_url: str, caption: str) -> str:
        r = self.session.post(
            f"{GRAPH}/{self.user_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": self.access_token,
            },
        )
        if not r.ok:
            raise RuntimeError(f"Error creant container ({r.status_code}): {r.text}")
        return r.json()["id"]

    def _wait_ready(self, creation_id: str, attempts: int = 10, delay: int = 3):
        """Espera que el container estigui FINISHED abans de publicar."""
        for _ in range(attempts):
            r = self.session.get(
                f"{GRAPH}/{creation_id}",
                params={"fields": "status_code", "access_token": self.access_token},
            )
            status = r.json().get("status_code")
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError(f"El container ha fallat: {r.text}")
            time.sleep(delay)
        # Si no arriba a FINISHED, provem igualment de publicar

    def _publish(self, creation_id: str) -> dict:
        r = self.session.post(
            f"{GRAPH}/{self.user_id}/media_publish",
            data={"creation_id": creation_id, "access_token": self.access_token},
        )
        if not r.ok:
            raise RuntimeError(f"Error publicant ({r.status_code}): {r.text}")
        return r.json()

    def publish_photo(self, image_url: str, caption: str) -> dict:
        creation_id = self._create_container(image_url, caption)
        self._wait_ready(creation_id)
        return self._publish(creation_id)

    # ── Renovació del token (60 dies) ─────────────────────────────────────────

    def refresh_token(self) -> str | None:
        """Renova el token de llarga durada. Retorna el nou token o None si falla."""
        r = self.session.get(
            f"{GRAPH_ROOT}/refresh_access_token",
            params={"grant_type": "ig_refresh_token", "access_token": self.access_token},
        )
        if not r.ok:
            print(f"   Avís: no s'ha pogut renovar el token ({r.status_code}): {r.text}")
            return None
        return r.json().get("access_token")
