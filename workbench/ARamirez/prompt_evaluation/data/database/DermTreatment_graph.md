### The high-level graph `DermTreatment` collection contains the following collections:
- **Doctors**: Contains information about doctors.
- **Patients**: Contains information about patients.
- **Drugs**: Contains information about drugs used in treatments.
- **Diagnoses**: Contains information about medical diagnoses.
- **Treatments**: Contains records of treatments administered.
- **Outcomes**: Contains records of treatment outcomes.
- **ConcomitantMeds**: Contains records of concomitant medications taken during treatments.
- **AdverseEvents**: Contains records of adverse events reported during treatments.

### The `Doctors` collection contains the following columns:
- **doc_id**: A unique identifier for the doctor.
- **first_name**: The first name of the doctor.
- **last_name**: The last name of the doctor.
- **speciality**: The medical specialty of the doctor (from `specialty`).
- **year_reg**: The year the doctor was registered.
- **med_school_name**: The name of the medical school the doctor attended.
- **loc_city**: The city where the doctor practices.
- **loc_state**: The state where the doctor practices.
- **loc_zip**: The ZIP code where the doctor practices.
- **bd_cert_num**: The board certification number of the doctor.
- **prescribed_treatments**: The corresponding treatments prescribed by this doctor (reverse of `Treatments.doctor`).

### The `Patients` collection contains the following columns:
- **patient_id**: A unique identifier for the patient.
- **first_name**: The first name of the patient.
- **last_name**: The last name of the patient.
- **date_of_birth**: The patient's date of birth.
- **date_of_registration**: The date the patient registered.
- **gender**: The gender of the patient.
- **email**: The email address of the patient.
- **phone**: The phone number of the patient.
- **addr_city**: The city of the patient's address.
- **addr_state**: The state of the patient's address.
- **addr_zip**: The ZIP code of the patient's address.
- **ins_type**: The type of insurance the patient has.
- **ins_policy_num**: The patient's insurance policy number.
- **height_cm**: The patient's height in centimeters.
- **weight_kg**: The patient's weight in kilograms.
- **treatments_received**: A list of all treatments received by this patient (reverse of `Treatments.patient`).

### The `Drugs` collection contains the following columns:
- **drug_id**: A unique identifier for the drug.
- **drug_name**: The name of the drug.
- **manufacturer**: The manufacturer of the drug.
- **drug_type**: The type or category of the drug.
- **moa**: The mechanism of action for the drug.
- **fda_appr_dt**: The date the drug was approved by the FDA.
- **admin_route**: The administration route for the drug (e.g., 'Oral', 'Topical').
- **dos_amt**: The standard dosage amount.
- **dos_unit**: The unit for the dosage amount (e.g., 'mg').
- **dos_freq_hrs**: The standard dosage frequency in hours.
- **ndc**: The National Drug Code.
- **treatments_used_in**: A list of all treatments this drug was used in (reverse of `Treatments.drug`).

### The `Diagnoses` collection contains the following columns:
- **diag_id**: A unique identifier for the diagnosis.
- **diag_code**: The standardized code for the diagnosis (e.g., ICD-10 code).
- **diag_name**: The name of the diagnosis.
- **diag_desc**: A description of the diagnosis.
- **treatments_for**: A list of all treatments associated with this diagnosis (reverse of `Treatments.diagnosis`).

### The `Treatments` collection contains the following columns:
- **treatment_id**: A unique identifier for the treatment record.
- **patient_id**: Foreign key referencing the `Patients` collection.
- **doc_id**: Foreign key referencing the `Doctors` collection.
- **drug_id**: Foreign key referencing the `Drugs` collection.
- **diag_id**: Foreign key referencing the `Diagnoses` collection.
- **start_dt**: The start date of the treatment.
- **end_dt**: The end date of the treatment.
- **is_placebo**: A flag indicating if the treatment was a placebo.
- **tot_drug_amt**: The total amount of the drug administered during the treatment.
- **drug_unit**: The unit for the total drug amount.
- **doctor**: The corresponding doctor who prescribed the treatment (reverse of `Doctors.prescribed_treatments`).
- **patient**: The corresponding patient who received the treatment (reverse of `Patients.treatments_received`).
- **drug**: The corresponding drug used in the treatment (reverse of `Drugs.treatments_used_in`).
- **diagnosis**: The corresponding diagnosis for which the treatment was administered (reverse of `Diagnoses.treatments_for`).
- **outcome_records**: A list of all outcome records associated with this treatment (reverse of `Outcomes.treatment`).
- **concomitant_meds**: A list of all concomitant medications taken during this treatment (reverse of `ConcomitantMeds.treatment`).
- **adverse_events**: A list of all adverse events reported during this treatment (reverse of `AdverseEvents.treatment`).

### The `Outcomes` collection contains the following columns:
- **outcome_id**: A unique identifier for the outcome record.
- **treatment_id**: Foreign key referencing the `Treatments` collection.
- **assess_dt**: The date the outcome assessment was performed.
- **day7_lesion_cnt**: Lesion count at day 7.
- **day30_lesion_cnt**: Lesion count at day 30.
- **day100_lesion_cnt**: Lesion count at day 100.
- **day7_pasi_score**: PASI score at day 7.
- **day30_pasi_score**: PASI score at day 30.
- **day100_pasi_score**: PASI score at day 100.
- **day7_tewl**: TEWL (Transepidermal Water Loss) measure at day 7.
- **day30_tewl**: TEWL measure at day 30.
- **day100_tewl**: TEWL measure at day 100.
- **day7_itch_vas**: Itch VAS (Visual Analog Scale) score at day 7.
- **day30_itch_vas**: Itch VAS score at day 30.
- **day100_itch_vas**: Itch VAS score at day 100.
- **day7_hfg**: HFG (Hair Follicle Grading) score at day 7.
- **day30_hfg**: HFG score at day 30.
- **day100_hfg**: HFG score at day 100.
- **treatment**: The corresponding treatment for this outcome record (reverse of `Treatments.outcome_records`).

### The `ConcomitantMeds` collection contains the following columns:
- **_id**: A unique identifier for the concomitant medication record.
- **treatment_id**: Foreign key referencing the `Treatments` collection.
- **med_name**: The name of the concomitant medication.
- **start_dt**: The start date of taking the medication.
- **end_dt**: The end date of taking the medication.
- **dose_amt**: The dosage amount of the medication.
- **dose_unit**: The unit for the dosage amount.
- **freq_hrs**: The frequency of dosage in hours.
- **treatment**: The corresponding treatment during which this medication was taken (reverse of `Treatments.concomitant_meds`).

### The `AdverseEvents` collection contains the following columns:
- **_id**: A unique identifier for the adverse event record.
- **treatment_id**: Foreign key referencing the `Treatments` collection.
- **reported_dt**: The date the adverse event was reported.
- **description**: A description of the adverse event.
- **treatment**: The corresponding treatment during which this adverse event occurred (reverse of `Treatments.adverse_events`).
