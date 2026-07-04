# Dentistry Module

## Workflow
- Create a dental record linked to a patient and EMR encounter.
- Maintain a dental chart with tooth-level condition notes.
- Record procedures, orthodontic cases, and uploaded images.

## Dental chart structure
- Tooth number and numbering system.
- Condition, caries, missing/filled teeth, crown/bridge, implant, root canal, mobility, and periodontal notes.

## Procedure workflow
- Create a dental procedure with diagnosis, treatment details, materials, notes, follow-up, and cost placeholder.
- Link the procedure to the dental record and patient chart.

## Orthodontic workflow
- Create orthodontic cases with diagnosis, malocclusion class, appliance type, treatment plan, and progress notes.
- Track follow-up visits and statuses.

## Image handling
- Upload intraoral images and X-rays.
- Validate file extension and store the file under a safe uploads/dentistry path.

## EMR integration
- Dental records are linked to the central patient record and can be used alongside other EMR modules.
- The dentistry module uses the same authentication and audit patterns as the rest of iHIS.

## Permissions
- Dentist and authorized doctors can manage dental records.
- Receptionists can book appointments only.
- Patients can view their own approved dental records.
- Admin and Super Admin can access all dentistry records.

## Audit logging
- Dental record creation and updates.
- Dental chart updates.
- Procedure creation and updates.
- Orthodontic case updates.
- Image upload events.
