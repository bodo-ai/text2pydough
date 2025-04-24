### The high-level graph `DATABASE` collection contains the following columns:
- **adverse_events**: A list of adverse_events.
- **concomitant_meds**: A list of concomitant_meds.
- **diagnoses**: A list of diagnoses.
- **doctors**: A list of doctors.
- **drugs**: A list of drugs.
- **outcomes**: A list of outcomes.
- **patients**: A list of patients.
- **treatments**: A list of treatments.

### The `adverse_events` collection contains the following columns:
- **id**: Id.
- **treatment_id**: Treatment id.
- **reported_dt**: Reported dt.
- **description**: Description.
- **treatment**: The corresponding treatments for this record (reverse of `treatments.adverse_events`).

### The `concomitant_meds` collection contains the following columns:
- **id**: Id.
- **treatment_id**: Treatment id.
- **med_name**: Med name.
- **start_dt**: Start dt.
- **end_dt**: End dt.
- **dose_amt**: Dose amt.
- **dose_unit**: Dose unit.
- **freq_hrs**: Freq hrs.
- **treatment**: The corresponding treatments for this record (reverse of `treatments.concomitant_meds`).

### The `diagnoses` collection contains the following columns:
- **diag_id**: Diag id.
- **diag_code**: Diag code.
- **diag_name**: Diag name.
- **diag_desc**: Diag desc.
- **treatments**: A list of all treatments associated with this record (reverse of `treatments.diagnose`).

### The `doctors` collection contains the following columns:
- **doc_id**: Doc id.
- **first_name**: First name.
- **last_name**: Last name.
- **specialty**: Specialty.
- **year_reg**: Year reg.
- **med_school_name**: Med school name.
- **loc_city**: Loc city.
- **loc_state**: Loc state.
- **loc_zip**: Loc zip.
- **bd_cert_num**: Bd cert num.
- **treatments**: A list of all treatments associated with this record (reverse of `treatments.doctor`).

### The `drugs` collection contains the following columns:
- **drug_id**: Drug id.
- **drug_name**: Drug name.
- **manufacturer**: Manufacturer.
- **drug_type**: Drug type.
- **moa**: Moa.
- **fda_appr_dt**: Fda appr dt.
- **admin_route**: Admin route.
- **dos_amt**: Dos amt.
- **dos_unit**: Dos unit.
- **dos_freq_hrs**: Dos freq hrs.
- **ndc**: Ndc.
- **treatments**: A list of all treatments associated with this record (reverse of `treatments.drug`).

### The `outcomes` collection contains the following columns:
- **outcome_id**: Outcome id.
- **treatment_id**: Treatment id.
- **assess_dt**: Assess dt.
- **day7_lesion_cnt**: Day7 lesion cnt.
- **day30_lesion_cnt**: Day30 lesion cnt.
- **day100_lesion_cnt**: Day100 lesion cnt.
- **day7_pasi_score**: Day7 pasi score.
- **day30_pasi_score**: Day30 pasi score.
- **day100_pasi_score**: Day100 pasi score.
- **day7_tewl**: Day7 tewl.
- **day30_tewl**: Day30 tewl.
- **day100_tewl**: Day100 tewl.
- **day7_itch_vas**: Day7 itch vas.
- **day30_itch_vas**: Day30 itch vas.
- **day100_itch_vas**: Day100 itch vas.
- **day7_hfg**: Day7 hfg.
- **day30_hfg**: Day30 hfg.
- **day100_hfg**: Day100 hfg.
- **treatment**: The corresponding treatments for this record (reverse of `treatments.outcomes`).

### The `patients` collection contains the following columns:
- **patient_id**: Patient id.
- **first_name**: First name.
- **last_name**: Last name.
- **date_of_birth**: Date of birth.
- **date_of_registration**: Date of registration.
- **gender**: Gender.
- **email**: The email
- **phone**: The phone number
- **addr_street**: Addr street.
- **addr_city**: Addr city.
- **addr_state**: Addr state.
- **addr_zip**: Addr zip.
- **ins_type**: Ins type.
- **ins_policy_num**: Ins policy num.
- **height_cm**: Height cm.
- **weight_kg**: Weight kg.
- **treatments**: A list of all treatments associated with this record (reverse of `treatments.patient`).

### The `treatments` collection contains the following columns:
- **treatment_id**: Treatment id.
- **patient_id**: Patient id.
- **doc_id**: Doc id.
- **drug_id**: Drug id.
- **diag_id**: Diag id.
- **start_dt**: Start dt.
- **end_dt**: End dt.
- **is_placebo**: Is placebo.
- **tot_drug_amt**: Tot drug amt.
- **drug_unit**: Drug unit.
- **adverse_events**: A list of all adverse_events associated with this record (reverse of `adverse_events.treatment`).
- **concomitant_meds**: A list of all concomitant_meds associated with this record (reverse of `concomitant_meds.treatment`).
- **outcomes**: A list of all outcomes associated with this record (reverse of `outcomes.treatment`).
- **diagnose**: The corresponding diagnoses for this record (reverse of `diagnoses.treatments`).
- **doctor**: The corresponding doctors for this record (reverse of `doctors.treatments`).
- **drug**: The corresponding drugs for this record (reverse of `drugs.treatments`).
- **patient**: The corresponding patients for this record (reverse of `patients.treatments`).

### Example Relationship Queries (Auto-generated)

To get the corresponding `treatments` for each `adverse_events`:
```python
adverse_events.treatment.CALCULATE(treatment_id, patient_id, doc_id, drug_id, diag_id, start_dt)
```

To get the corresponding `treatments` for each `concomitant_meds`:
```python
concomitant_meds.treatment.CALCULATE(treatment_id, patient_id, doc_id, drug_id, diag_id, start_dt)
```

To get all `treatments` from each `diagnoses`:
```python
diagnoses.treatments.CALCULATE(diag_id, diag_code, diag_name, diag_desc)
```

To get all `treatments` from each `doctors`:
```python
doctors.treatments.CALCULATE(doc_id, first_name, last_name, specialty, year_reg, med_school_name)
```

To get all `treatments` from each `drugs`:
```python
drugs.treatments.CALCULATE(drug_id, drug_name, manufacturer, drug_type, moa, fda_appr_dt)
```

To get the corresponding `treatments` for each `outcomes`:
```python
outcomes.treatment.CALCULATE(treatment_id, patient_id, doc_id, drug_id, diag_id, start_dt)
```

To get all `treatments` from each `patients`:
```python
patients.treatments.CALCULATE(patient_id, first_name, last_name, date_of_birth, date_of_registration, gender)
```

To get all `adverse_events` from each `treatments`:
```python
treatments.adverse_events.CALCULATE(treatment_id, patient_id, doc_id, drug_id, diag_id, start_dt)
```

To get all `concomitant_meds` from each `treatments`:
```python
treatments.concomitant_meds.CALCULATE(treatment_id, patient_id, doc_id, drug_id, diag_id, start_dt)
```

To get all `outcomes` from each `treatments`:
```python
treatments.outcomes.CALCULATE(treatment_id, patient_id, doc_id, drug_id, diag_id, start_dt)
```

To get the corresponding `diagnoses` for each `treatments`:
```python
treatments.diagnose.CALCULATE(diag_id, diag_code, diag_name, diag_desc)
```

To get the corresponding `doctors` for each `treatments`:
```python
treatments.doctor.CALCULATE(doc_id, first_name, last_name, specialty, year_reg, med_school_name)
```

To get the corresponding `drugs` for each `treatments`:
```python
treatments.drug.CALCULATE(drug_id, drug_name, manufacturer, drug_type, moa, fda_appr_dt)
```

To get the corresponding `patients` for each `treatments`:
```python
treatments.patient.CALCULATE(patient_id, first_name, last_name, date_of_birth, date_of_registration, gender)
```
