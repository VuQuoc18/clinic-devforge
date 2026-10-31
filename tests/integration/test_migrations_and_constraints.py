from datetime import datetime, timezone

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError

from app.models import PatientAccount, PatientProfile, StaffAccount
from tests.conftest import alembic_config

TABLES = {"patient_accounts", "patient_profiles", "staff_accounts", "otp_codes", "otp_counters"}


def test_migration_upgrade_and_rollback(db_url):
    cfg = alembic_config(db_url)
    engine = create_engine(db_url)
    command.upgrade(cfg, "head")
    assert TABLES <= set(inspect(engine).get_table_names())
    command.downgrade(cfg, "base")
    assert not (TABLES & set(inspect(engine).get_table_names()))
    command.upgrade(cfg, "head")  # re-apply cleanly
    assert TABLES <= set(inspect(engine).get_table_names())


def test_db_columns_match_req_026(migrated_engine):
    insp = inspect(migrated_engine)
    names = lambda t: {c["name"] for c in insp.get_columns(t)}
    assert {"phone", "created_at", "online_booking_locked", "lock_expires_at",
            "consented_policy_version", "consented_at"} <= names("patient_accounts")
    assert {"full_name", "date_of_birth", "gender", "phone", "email", "address",
            "relationship", "is_owner", "is_hidden"} <= names("patient_profiles")
    assert {"full_name", "email", "role", "status", "last_login_at"} <= names("staff_accounts")


def test_duplicate_patient_phone_rejected(session):
    session.add(PatientAccount(phone="0901234567"))
    session.commit()
    session.add(PatientAccount(phone="0901234567"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_duplicate_staff_email_rejected(session):
    session.add(StaffAccount(full_name="A", email="a@clinic.vn", role="admin"))
    session.commit()
    session.add(StaffAccount(full_name="B", email="a@clinic.vn", role="doctor"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_defaults_and_profile_roundtrip(session):
    acc = PatientAccount(phone="0911111111")
    acc.profiles.append(PatientProfile(full_name="Nguyen Van A", is_owner=True))
    session.add(acc)
    session.commit()
    session.refresh(acc)
    assert acc.online_booking_locked is False
    assert acc.lock_expires_at is None
    p = acc.profiles[0]
    assert p.is_owner is True and p.is_hidden is False
    staff = StaffAccount(full_name="S", email="s@clinic.vn", role="receptionist")
    session.add(staff)
    session.commit()
    assert staff.status == "active"


def test_profile_requires_existing_account(session):
    session.add(PatientProfile(account_id=999, full_name="X"))
    with pytest.raises(IntegrityError):
        session.commit()
