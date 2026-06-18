import json
from sqlalchemy.orm import Session
from ..models import User, Zone
from ..schemas import ZoneIn
from ..utils.time_utils import utc_iso


def serialize_zone(zone: Zone) -> dict:
    return {
        "id": zone.id,
        "name": zone.name,
        "zone_type": zone.zone_type,
        "coordinates": json.loads(zone.coordinates),
        "source_type": zone.source_type,
        "created_at": utc_iso(zone.created_at),
    }


def list_zones(db: Session, user: User) -> list[Zone]:
    return db.query(Zone).filter(Zone.user_id == user.id).order_by(Zone.created_at.desc()).all()


def create_zone(db: Session, user: User, payload: ZoneIn) -> Zone:
    zone = Zone(
        user_id=user.id,
        name=payload.name,
        zone_type=payload.zone_type,
        coordinates=json.dumps(payload.coordinates),
        source_type=payload.source_type,
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone
