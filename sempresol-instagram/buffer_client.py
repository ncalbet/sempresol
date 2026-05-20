"""
buffer_client.py
Client per a l'API v1 de Buffer.
"""

import os
import requests

BUFFER_API_BASE = "https://api.bufferapp.com/1"


class BufferClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["BUFFER_API_KEY"]
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
        })

    def get_profiles(self) -> list[dict]:
        r = self.session.get(f"{BUFFER_API_BASE}/profiles.json")
        r.raise_for_status()
        return r.json()

    def get_instagram_profile_id(self) -> str:
        profile_id = os.environ.get("BUFFER_PROFILE_ID")
        if profile_id:
            return profile_id
        profiles = self.get_profiles()
        for p in profiles:
            if p.get("service") in ("instagram", "instagram_business"):
                return p["id"]
        raise ValueError(
            "No s'ha trobat cap perfil d'Instagram a Buffer. "
            "Defineix BUFFER_PROFILE_ID a les secrets de GitHub."
        )

    def add_to_queue(
        self,
        profile_id: str,
        text: str,
        image_path: str | None = None,
        image_url: str | None = None,
        scheduled_at: str | None = None,
    ) -> dict:
        payload: dict = {
            "access_token":  self.api_key,
            "profile_ids[]": profile_id,
            "text":          text,
        }

        if scheduled_at:
            payload["scheduled_at"] = scheduled_at

        if image_url:
            payload["media[photo]"] = image_url

        r = self.session.post(
            f"{BUFFER_API_BASE}/updates/create.json",
            data=payload,
        )
        if not r.ok:
            print(f"   Resposta Buffer ({r.status_code}): {r.text[:500]}")
        r.raise_for_status()
        return r.json()
