"""Phase 10 Women's Health workflow tests."""
from datetime import date, datetime, timedelta, timezone
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from extensions import db
from models import (Doctor, Patient, Permission, Role, Specialty, User,
                    WomensHealthApproval, WomensUltrasoundAttachment)
from services.emr_service import build_patient_timeline
from services.womens_health import *
from services.womens_health.ultrasound_service import attach_ultrasound_file


def user(session,name,role_name,permissions=()):
    role=session.scalar(db.select(Role).where(Role.name==role_name)) or Role(name=role_name)
    for code in permissions:
        permission=session.scalar(db.select(Permission).where(Permission.code==code)) or Permission(code=code,module="womens_health",action=code.split(".")[-1])
        if permission not in role.permissions: role.permissions.append(permission)
    value=User(username=name,email=f"{name}@test.local",first_name=name.title(),last_name="Test",roles=[role]); value.set_password("test-password")
    session.add(value); session.commit(); return value


def context(session):
    clinician=user(session,"whdoctor","Women’s Health Doctor",("womens_health.view","womens_health.create","womens_health.update","womens_health.sign"))
    specialty=Specialty(code="WH10",name="Women's Health Phase 10")
    doctor=Doctor(user=clinician,specialty=specialty,license_number="WH10-LIC")
    patient=Patient(medical_record_number="MR-WH10",first_name="Mariam",last_name="Patient",date_of_birth=date(1992,2,2),sex_at_birth="female")
    session.add_all([specialty,doctor,patient]); session.commit()
    profile=create_womens_health_profile(patient,actor=clinician,ob_gyn_summary="Initial summary")
    return clinician,patient,profile


def test_profile_and_pregnancy_creation(session):
    clinician,patient,profile=context(session)
    pregnancy=create_pregnancy(profile,actor=clinician,lmp=date.today()-timedelta(days=70),gravida=1,para=0)
    assert patient.womens_health_profile is profile
    assert pregnancy.estimated_due_date==pregnancy.lmp+timedelta(days=280)
    assert profile.active_journey_id==pregnancy.id
    assert any(event.event_type=="pregnancy_created" for event in build_womens_health_timeline(profile))


def test_ga_edd_cycle_day_and_bmi_calculations():
    lmp=date(2026,1,1)
    assert calculate_edd(lmp)==date(2026,10,8)
    assert calculate_ga(lmp=lmp,on_date=date(2026,3,12))=={"weeks":10,"days":0,"total_days":70}
    assert calculate_ga(edd=date(2026,10,8),on_date=date(2026,3,12))["weeks"]==10
    assert calculate_cycle_day(date(2026,3,1),date(2026,3,5))==5
    assert str(calculate_bmi(60,160))=="23.44"


def test_anc_links_to_pregnancy_and_nurse_is_vitals_only(session):
    clinician, _, profile = context(session)
    visit_at = datetime(2026, 7, 5, 10, 0, tzinfo=timezone.utc)

    pregnancy = create_pregnancy(
        profile,
        actor=clinician,
        lmp=visit_at.date() - timedelta(days=84),
    )

    nurse = user(
        session,
        "whnurse",
        "Nurse",
        ("womens_health.record_anc_basic",),
    )

    anc = create_antenatal_visit(
        pregnancy,
        actor=nurse,
        visit_at=visit_at,
        weight_kg=65,
        systolic_bp=110,
        diastolic_bp=70,
        fetal_heart_rate=145,
    )

    assert anc.pregnancy is pregnancy
    assert anc.pregnancy_visit.gestational_age_weeks == 12

    with pytest.raises(PermissionError):
        create_antenatal_visit(
            pregnancy,
            actor=nurse,
            assessment="Clinical decision",
        )


def test_ultrasound_links_and_secure_attachment(app,session):
    clinician,_,profile=context(session); pregnancy=create_pregnancy(profile,actor=clinician,lmp=date.today()-timedelta(days=90))
    report=create_womens_ultrasound(profile,actor=clinician,scan_type="obstetric",pregnancy=pregnancy,impression="Viable pregnancy",placenta="Posterior",liquor="Normal",biometry=[{"biparietal_diameter_mm":25}],dopplers=[{"vessel":"umbilical_artery","pulsatility_index":1.1}])
    storage=FileStorage(stream=BytesIO(b"%PDF safe report"),filename="scan.pdf",content_type="application/pdf")
    attachment=attach_ultrasound_file(report,storage,actor=clinician)
    assert report.pregnancy is pregnancy and attachment.checksum_sha256
    assert len(report.fetal_biometry)==1 and len(report.doppler_records)==1
    assert session.get(WomensUltrasoundAttachment,attachment.id)


def test_gynecology_and_infertility_workflows(session):
    clinician,_,profile=context(session)
    gyn=create_gynecology_journey(profile,actor=clinician,primary_condition="Abnormal bleeding")
    visit=create_gynecology_visit(gyn,actor=clinician,diagnosis="AUB",procedures=["Pelvic examination"])
    journey=create_infertility_journey(profile,actor=clinician,infertility_type="primary",duration_months=18,treatment_plan="OITI")
    cycle=create_infertility_cycle(journey,actor=clinician,cycle_type="oiti",cycle_start_date=date.today()-timedelta(days=9))
    record=add_folliculometry_record(cycle,actor=clinician,endometrium_mm=8)
    follicle=add_follicle_measurement(record,actor=clinician,ovary="right",follicle_number=1,diameter_mm=18)
    assert visit.journey is gyn and record.cycle is cycle and follicle.record is record


def test_partner_semen_analysis_and_iui(session):
    clinician,_,profile=context(session); journey=create_infertility_journey(profile,actor=clinician,infertility_type="secondary")
    partner=create_partner_record(journey,actor=clinician,first_name="Omar",last_name="Test")
    analysis=add_semen_analysis(partner,actor=clinician,volume_ml=3,concentration_million_ml=30)
    cycle=create_infertility_cycle(journey,actor=clinician,cycle_type="iui",cycle_start_date=date.today())
    iui=create_iui_cycle(cycle,actor=clinician,partner_id=partner.id,semen_analysis_id=analysis.id,performed_at=datetime.now(timezone.utc),semen_preparation_summary="Prepared")
    assert analysis.partner is partner and iui.cycle is cycle and iui.partner_id==partner.id


def test_signed_records_filter_patient_timeline(session):
    clinician,_,profile=context(session); pregnancy=create_pregnancy(profile,actor=clinician,lmp=date.today()-timedelta(days=30))
    assert not build_womens_health_timeline(profile,signed_only=True)
    sign_record(pregnancy,profile,actor=clinician)
    visible=build_womens_health_timeline(profile,signed_only=True)
    assert len(visible)==1 and visible[0].source_id==pregnancy.id
    central=build_patient_timeline(profile.patient,signed_womens_health_only=True)
    assert any(event["kind"]=="womens_health" for event in central)


def test_patient_sees_only_own_signed_profile(client,session):
    clinician,patient,profile=context(session); portal=user(session,"whpatient","Patient"); patient.user_id=portal.id
    sign_record(profile,profile,actor=clinician); session.commit()
    other=Patient(medical_record_number="MR-WH-OTHER",first_name="Other",last_name="Patient",date_of_birth=date(1990,1,1),sex_at_birth="female")
    session.add(other); session.commit()
    client.post("/auth/login",data={"identifier":portal.username,"password":"test-password"})
    assert client.get(f"/patients/{patient.id}/womens-health").status_code==200
    assert client.get(f"/patients/{other.id}/womens-health").status_code==403


def test_unauthorized_user_cannot_edit_womens_health(client,session):
    _,patient,_=context(session); receptionist=user(session,"whreception","Receptionist")
    client.post("/auth/login",data={"identifier":receptionist.username,"password":"test-password"})
    assert client.get(f"/patients/{patient.id}/pregnancies/create").status_code==403


def test_dashboard_and_clinical_pages_render(client,session):
    clinician,patient,profile=context(session)
    pregnancy=create_pregnancy(profile,actor=clinician,lmp=date.today()-timedelta(days=40))
    client.post("/auth/login",data={"identifier":clinician.username,"password":"test-password"})
    assert client.get("/womens-health").status_code==200
    assert client.get(f"/patients/{patient.id}/womens-health").status_code==200
    assert client.get(f"/pregnancies/{pregnancy.id}").status_code==200
    assert client.get("/womens-ultrasound/create").status_code==200


def test_profile_update_returns_signed_record_to_draft(session):
    clinician,_,profile=context(session)
    sign_record(profile,profile,actor=clinician)
    update_womens_health_profile(profile,actor=clinician,ob_gyn_summary="Changed after signing")
    approval=session.scalar(db.select(WomensHealthApproval).where(WomensHealthApproval.source_id==profile.id))
    assert approval.status=="draft" and approval.signed_at is None
