from fastapi import Request

from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres


def get_pg(request: Request) -> SupabasePostgres:
    return request.app.state.pg


def get_d1(request: Request) -> D1Client:
    return request.app.state.d1
