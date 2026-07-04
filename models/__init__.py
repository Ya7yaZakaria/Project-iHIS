"""Complete iHIS model registry used by SQLAlchemy and Flask-Migrate."""

from .user import (AIRecommendation, AuditLog, Department, Message, Notification,
                   Permission, Role, SystemSetting, User, role_permissions, user_roles)
from .patient import Appointment, Patient
from .doctor import Doctor, Specialty
from .emr import (Diagnosis, MedicalAttachment, MedicalRecord, Medication,
                  NursingNote, Prescription, PrescriptionItem, VitalSign)
from .laboratory import LabOrder, LabResult, LabTest
from .radiology import (
    ImagingStudy,
    RadiologyAttachment,
    RadiologyOrder,
    RadiologyReport,
)
from .pharmacy import (DispensingRecord, PatientMedicationHistory,
                       PharmacyInventory, StockMovement)
from .dentistry import (DentalChart, DentalImage, DentalProcedure, DentalRecord,
                        DentalSpecialty, Dentist, OrthodonticCase)
from .rehabilitation import (CareTeam, ExerciseLibrary, FunctionalOutcome,
                             MultidisciplinaryCase, PhysicalTherapist, Referral,
                             RehabilitationProgress, TherapyAssessment,
                             TherapyExercise, TherapyPlan, TherapySession, care_team_members)
from .womens_health import (AntenatalVisit, DeliveryRecord, FetalBiometry,
                            FetalDopplerRecord, FertilityMedicationProtocol,
                            FollicleMeasurement, FolliculometryRecord,
                            GynecologyJourney, GynecologyUltrasoundRecord,
                            GynecologyVisit, InfertilityCycle, InfertilityJourney,
                            IUICycle, ObstetricHistory, OvulationInductionCycle,
                            PartnerRecord, PostpartumVisit, Pregnancy,
                            PregnancyRiskFlag, PregnancyVisit, SemenAnalysis,
                            WomensHealthCalculation, WomensHealthProfile,
                            WomensHealthApproval, WomensHealthTimelineEvent,
                            WomensUltrasoundAttachment, WomensUltrasoundReport)

__all__ = [name for name in globals() if not name.startswith("_")]
