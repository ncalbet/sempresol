"""
buffer_client.py
Client mínim per a l'API beta de Buffer.
Documentació oficial: https://publish.buffer.com/account/apps
"""

import os
import base64
import requests


BUFFER_API_BASE = "https://api.bufferapp.com/1"


class BufferClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["BUFFER_API_KEY"]
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
        })

    # ── Perfils ───────────────────────────────────────────────────────────────

    def get_profiles(self) -> list[dict]:
        """Retorna tots els perfils connectats al compte Buffer."""
        r = self.session.get(f"{BUFFER_API_BASE}/profiles.json")
        r.raise_for_status()
        return r.json()

    def get_instagram_profile_id(self) -> str:
        """
        Retorna l'ID del primer perfil d'Instagram trobat.
        Si tens l'ID guardat a BUFFER_PROFILE_ID, l'usa directament.
        """
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

    # ── Imatges ───────────────────────────────────────────────────────────────

    def upload_image(self, image_path: str) -> str:
        """
        Puja una imatge a Buffer i retorna el media ID o URL.
        (Beta API: comprova la documentació per al teu pla)
        """
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Intenta endpoint de pujada de media
        r = self.session.post(
            f"{BUFFER_API_BASE}/media/upload",
            json={"image": base64.b64encode(image_data).decode("utf-8")},
        )

        if r.ok:
            data = r.json()
            return data.get("id") or data.get("url", "")

        # Alternativa: usa URL pública de GitHub (si el repo és públic)
        # Retorna cadena buida i el main.py gestionarà el fallback
        print(f"⚠️  Upload d'imatge no disponible: {r.status_code} {r.text[:200]}")
        return ""

    # ── Publicació ────────────────────────────────────────────────────────────

    def add_to_queue(
        self,
        profile_id: str,
        text: str,
        image_path: str | None = None,
        image_url: str | None = None,
        scheduled_at: str | None = None,
    ) -> dict:
        """
        Afegeix un post a la cua de Buffer.

        Args:
            profile_id:   ID del perfil Instagram a Buffer.
            text:         Caption del post (amb hashtags).
            image_path:   Ruta local de la imatge (opcional).
            image_url:    URL pública de la imatge (alternativa a image_path).
            scheduled_at: ISO 8601 UTC, p.ex. '2026-05-10T09:00:00Z'.
                          Si és None, s'afegeix al final de la cua.
        Returns:
            Resposta JSON de Buffer.
        """
        payload: dict = {
            "profile_ids[]": profile_id,
            "text":           text,
        }

        if scheduled_at:
            payload["scheduled_at"] = scheduled_at
            payload["now"]          = False
        else:
            payload["now"] = False   # afegeix a cua

        # Gestió d'imatge
        media_id = ""
        if image_path:
            media_id = self.upload_image(image_path)

        if media_id:
            payload["media[photo]"] = media_id
        elif image_url:
            payload["media[link]"]  = image_url
            payload["media[photo]"] = image_url

        # Endpoint principal de creació de post
        r = self.session.post(
            f"{BUFFER_API_BASE}/updates/create.json",
            data=payload,          # Buffer accepta form-data en aquest endpoint
            headers={},            # Elimina Content-Type JSON per a form-data
        )

        # Reintent amb endpoint beta si l'anterior falla
        if not r.ok:
            print(f"⚠️  Primer endpoint fallat ({r.status_code}). Provant endpoint beta…")
            r = self.session.post(
                "https://api.buffer.com/posts",
                json={
                    "profile_id":   profile_id,
                    "text":         text,
                    "scheduled_at": scheduled_at,
                    "media":        {"photo": image_url} if image_url else {},
                },
                headers={"Content-Type": "application/json"},
            )

        r.raise_for_status()
        return r.json()
