from typing import List

from ..schemas.biens import Bien, BienCreate
from ..core import supabase_client


def list_biens() -> List[Bien]:
    """Return all biens stored in the Supabase table."""
    client = supabase_client.get_supabase_client()
    resp = client.table("biens").select("*").execute()
    if resp.error:
        raise RuntimeError(resp.error)
    return [Bien(**item) for item in resp.data or []]


def create_bien(bien: BienCreate) -> Bien:
    """Insert a new bien into Supabase and return the created record."""
    client = supabase_client.get_supabase_client()
    resp = client.table("biens").insert(bien.dict()).execute()
    if resp.error:
        raise RuntimeError(resp.error)
    data = resp.data[0] if resp.data else {}
    return Bien(**data)
