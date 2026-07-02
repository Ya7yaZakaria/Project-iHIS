from datetime import date, datetime, timezone

from models import (InfertilityCycle, InfertilityJourney, Patient, Pregnancy,
                    WomensHealthProfile)


def test_profile_pregnancy_and_infertility_relationships(session):
    patient = Patient(medical_record_number="MRN-WH", first_name="Mariam", last_name="Adel", date_of_birth=date(1992, 2, 2), sex_at_birth="female")
    profile = WomensHealthProfile(patient=patient)
    pregnancy = Pregnancy(profile=profile, pregnancy_number=1, gravida=1, para=0, status="ongoing")
    journey = InfertilityJourney(journey_number="INF-001", profile=profile, infertility_type="primary", started_at=datetime.now(timezone.utc))
    cycle = InfertilityCycle(journey=journey, cycle_number=1, cycle_type="ovulation_induction", cycle_start_date=date.today())
    session.add_all([patient, profile, pregnancy, journey, cycle])
    session.commit()

    assert patient.womens_health_profile is profile
    assert pregnancy in profile.pregnancies
    assert cycle in journey.cycles
