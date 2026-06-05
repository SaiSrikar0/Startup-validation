from __future__ import annotations

from app.utils.supabase_client import get_supabase

supabase = get_supabase()


def list_startups():
    """
    Return all startups from Supabase.
    """

    response = (
        supabase
        .table("startups")
        .select("*")
        .execute()
    )

    return [db_to_api(row) for row in response.data]


def get_startup(startup_id: int):
    """
    Return a single startup by id.
    """

    response = (
        supabase
        .table("startups")
        .select("*")
        .eq("id", startup_id)
        .execute()
    )

    if not response.data:
        return None

    return db_to_api(response.data[0])


def create_startup(data: dict):
    """
    Insert a startup record.
    """

    response = (
        supabase
        .table("startups")
        .insert(data)
        .execute()
    )

    if not response.data:
        return None

    return db_to_api(response.data[0])


def update_startup(startup_id: int, updates: dict):
    """
    Update an existing startup.
    """

    response = (
        supabase
        .table("startups")
        .update(updates)
        .eq("id", startup_id)
        .execute()
    )

    if not response.data:
        return None

    return db_to_api(response.data[0])


def delete_startup(startup_id: int):
    """
    Delete a startup by id.
    """

    response = (
        supabase
        .table("startups")
        .delete()
        .eq("id", startup_id)
        .execute()
    )

    return len(response.data) > 0


def search_startups(
    status: str | None = None,
    country: str | None = None,
    company: str | None = None,
):
    """
    Basic filtering support.
    """

    query = (
        supabase
        .table("startups")
        .select("*")
    )

    if status:
        query = query.eq("status", status)

    if country:
        query = query.eq("headquarters_country", country)

    if company:
        query = query.ilike("company", f"%{company}%")

    response = query.execute()

    return [db_to_api(row) for row in response.data]


def startup_create_to_db(payload):

    return {
        "company": payload.company,
        "status": payload.status,
        "year_founded": payload.year_founded,
        "description": payload.description,
        "categories": ",".join(payload.categories),
        "founders": ",".join(payload.founders),
        "investors": ",".join(payload.investors),
        "funding_rounds": ",".join(payload.funding_rounds),
        "headquarters_city": payload.city,
        "headquarters_state": payload.state,
        "headquarters_country": payload.country,
    }


def startup_update_to_db(payload):

    data = payload.model_dump(exclude_unset=True)

    mapping = {}

    for key, value in data.items():

        if key == "city":
            mapping["headquarters_city"] = value

        elif key == "state":
            mapping["headquarters_state"] = value

        elif key == "country":
            mapping["headquarters_country"] = value

        elif isinstance(value, list):
            mapping[key] = ",".join(value)

        else:
            mapping[key] = value

    return mapping


def db_to_api(record: dict):

    return {
        "startup_id": str(record["id"]),
        "company": record["company"],
        "status": record["status"],
        "year_founded": record["year_founded"],
        "description": record["description"],

        "categories": (
            record["categories"].split(",")
            if record.get("categories")
            else []
        ),

        "founders": (
            record["founders"].split(",")
            if record.get("founders")
            else []
        ),

        "investors": (
            record["investors"].split(",")
            if record.get("investors")
            else []
        ),

        "funding_rounds": (
            record["funding_rounds"].split(",")
            if record.get("funding_rounds")
            else []
        ),

        "city": record.get("headquarters_city"),
        "state": record.get("headquarters_state"),
        "country": record.get("headquarters_country"),
    }