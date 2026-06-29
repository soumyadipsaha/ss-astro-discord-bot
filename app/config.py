import os


class Settings:
    @property
    def discord_public_key(self) -> str:
        return os.environ.get("DISCORD_PUBLIC_KEY", "")

    @property
    def discord_token(self) -> str:
        return os.environ.get("DISCORD_TOKEN", "")

    @property
    def discord_app_id(self) -> str:
        return os.environ.get("DISCORD_APP_ID", "")

    @property
    def ephe_path(self) -> str:
        return os.environ.get("EPHE_PATH", "")

    @property
    def ayanamsa_offset_arcmin(self) -> float:
        try:
            return float(os.environ.get("AYANAMSA_OFFSET_ARCMIN", "6") or 6)
        except ValueError:
            return 6.0


settings = Settings()
