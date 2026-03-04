from typing import List

from ..schemas.loyers import Loyer, LoyerCreate
from ..core import supabase_client


def list_loyers() -> List[Loyer]:
    client = supabase_client.get_supabase_client()
    resp = client.table("loyers").select("*").execute()
    if resp.error:
        raise RuntimeError(resp.error)
    return [Loyer(**item) for item in resp.data or []]


def create_loyer(loyer: LoyerCreate) -> Loyer:
    client = supabase_client.get_supabase_client()
    resp = client.table("loyers").insert(loyer.dict()).execute()
    if resp.error:
        raise RuntimeError(resp.error)
    data = resp.data[0] if resp.data else {}
    return Loyer(**data)
