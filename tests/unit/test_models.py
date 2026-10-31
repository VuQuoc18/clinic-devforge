from sqlalchemy import UniqueConstraint

from app.models import OtpCode, OtpCounter, PatientAccount, PatientProfile, StaffAccount


def cols(model):
    return {c.name for c in model.__table__.columns}


def test_patient_account_fields():
    assert {"phone", "created_at", "online_booking_locked", "lock_expires_at",
            "consented_policy_version", "consented_at"} <= cols(PatientAccount)
    assert PatientAccount.__table__.c.phone.nullable is False


def test_patient_profile_fields():
    assert {"full_name", "date_of_birth", "gender", "phone", "email", "address",
            "relationship", "is_owner", "is_hidden"} <= cols(PatientProfile)


def test_staff_account_fields():
    assert {"full_name", "email", "role", "status", "last_login_at"} <= cols(StaffAccount)


def test_unique_constraints_declared():
    def unique_cols(model):
        return [{c.name for c in con.columns} for con in model.__table__.constraints
                if isinstance(con, UniqueConstraint)]
    assert {"phone"} in unique_cols(PatientAccount)
    assert {"email"} in unique_cols(StaffAccount)
    assert {"phone", "window_start"} in unique_cols(OtpCounter)


def test_otp_fields():
    assert {"phone", "code_hash", "expires_at", "consumed_at", "attempt_count"} <= cols(OtpCode)
    assert {"send_count", "failed_count"} <= cols(OtpCounter)
