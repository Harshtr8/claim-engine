import json
from datetime import date
from typing import Any

import requests
import streamlit as st


# =========================================================
# CONFIG
# =========================================================

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Claim Decision Engine",
    page_icon="🛡️",
    layout="wide",
)


# =========================================================
# STYLING
# =========================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #666;
        margin-bottom: 1.5rem;
    }

    .decision-box {
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin: 1rem 0;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 650;
        margin-top: 1.2rem;
        margin-bottom: 0.7rem;
    }

    .small-note {
        color: #777;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DEMO CASES
# =========================================================

DEMO_CASES = {
    "Manual Input": None,

    "CUS-001 — Fully Admissible": {
        "case_id": "CUS-001",
        "policy_start_date": "2024-01-01",
        "claim_date": "2026-06-01",
        "hospitalization_start_date": "2026-06-01",
        "hospitalization_end_date": "2026-06-04",
        "diagnosis": "Appendicitis",
        "treatment": "Inpatient surgery and hospitalization",
        "domiciliary_treatment": False,
        "experimental": False,
        "hospital_name": "City Hospital",
        "hospital_registration": "REG-12345",
        "hospital_registered": True,
        "hospital_minimum_criteria_documented": True,
        "is_inpatient": True,
        "treatment_duration_hours": 72,
        "hospital_room_unavailable": False,
        "patient_cannot_be_moved": False,
        "medical_necessity_confirmed": True,
        "pre_existing_disease": False,
        "current_sum_insured": 500000,
        "claimed_amount": 144800,
        "room_expense": 12000,
        "icu_expense": 0,
        "doctor_expense": 40000,
        "medicine_diagnostic_expense": 80000,
        "pre_hospitalization_expense": 5000,
        "post_hospitalization_expense": 7000,
        "ambulance_expense": 800,
        "pre_hospitalization_days_before": 20,
        "post_hospitalization_days_after_discharge": 30,
        "same_condition_confirmed": True,
        "documents": [
            "claim_form",
            "hospital_bill",
            "discharge_summary",
        ],
        "evidence_context_present": True,
        "expense_timing_present": True,
        "prior_policy_present": False,
        "dataset_continuous_coverage_months": None,
        "additional_information": (
            "Complete hospitalization and billing evidence is available."
        ),
    },

    "CUS-002 — Admissible With Limits": {
        "case_id": "CUS-002",
        "policy_start_date": "2024-01-01",
        "claim_date": "2026-06-01",
        "hospitalization_start_date": "2026-06-01",
        "hospitalization_end_date": "2026-06-05",
        "diagnosis": "Pneumonia",
        "treatment": "Inpatient hospitalization and intensive care",
        "domiciliary_treatment": False,
        "experimental": False,
        "hospital_name": "City Hospital",
        "hospital_registration": "REG-12345",
        "hospital_registered": True,
        "hospital_minimum_criteria_documented": True,
        "is_inpatient": True,
        "treatment_duration_hours": 96,
        "hospital_room_unavailable": False,
        "patient_cannot_be_moved": False,
        "medical_necessity_confirmed": True,
        "pre_existing_disease": False,
        "current_sum_insured": 500000,
        "claimed_amount": 541500,
        "room_expense": 30000,
        "icu_expense": 60000,
        "doctor_expense": 200000,
        "medicine_diagnostic_expense": 250000,
        "pre_hospitalization_expense": 0,
        "post_hospitalization_expense": 0,
        "ambulance_expense": 1500,
        "pre_hospitalization_days_before": None,
        "post_hospitalization_days_after_discharge": None,
        "same_condition_confirmed": None,
        "documents": [
            "claim_form",
            "hospital_bill",
            "discharge_summary",
        ],
        "evidence_context_present": True,
        "expense_timing_present": False,
        "prior_policy_present": False,
        "dataset_continuous_coverage_months": None,
        "additional_information": (
            "Complete hospitalization and billing evidence is available."
        ),
    },

    "CUS-003 — Pre-existing Disease": {
        "case_id": "CUS-003",
        "policy_start_date": "2024-01-01",
        "claim_date": "2026-06-01",
        "hospitalization_start_date": "2026-06-01",
        "hospitalization_end_date": "2026-06-04",
        "diagnosis": "Diabetes Mellitus",
        "treatment": "Inpatient hospitalization",
        "domiciliary_treatment": False,
        "experimental": False,
        "hospital_name": "City Hospital",
        "hospital_registration": "REG-12345",
        "hospital_registered": True,
        "hospital_minimum_criteria_documented": True,
        "is_inpatient": True,
        "treatment_duration_hours": 72,
        "hospital_room_unavailable": False,
        "patient_cannot_be_moved": False,
        "medical_necessity_confirmed": True,
        "pre_existing_disease": True,
        "pre_existing_details": "Known diabetes before policy inception.",
        "current_sum_insured": 500000,
        "claimed_amount": 55000,
        "room_expense": 10000,
        "icu_expense": 0,
        "doctor_expense": 15000,
        "medicine_diagnostic_expense": 30000,
        "pre_hospitalization_expense": 0,
        "post_hospitalization_expense": 0,
        "ambulance_expense": 0,
        "documents": [
            "claim_form",
            "hospital_bill",
        ],
        "evidence_context_present": False,
        "expense_timing_present": False,
        "prior_policy_present": False,
        "dataset_continuous_coverage_months": None,
        "additional_information": (
            "Pre-existing disease is declared in the claim."
        ),
    },

    "CUS-004 — Needs Review": {
        "case_id": "CUS-004",
        "policy_start_date": "2024-01-01",
        "claim_date": "2026-06-01",
        "hospitalization_start_date": "2026-06-01",
        "hospitalization_end_date": "2026-06-04",
        "diagnosis": "Gallbladder infection",
        "treatment": "Inpatient hospitalization",
        "domiciliary_treatment": False,
        "experimental": False,
        "hospital_name": "Unknown Hospital",
        "hospital_registration": None,
        "hospital_registered": None,
        "hospital_minimum_criteria_documented": None,
        "is_inpatient": True,
        "treatment_duration_hours": 72,
        "hospital_room_unavailable": False,
        "patient_cannot_be_moved": False,
        "medical_necessity_confirmed": None,
        "pre_existing_disease": False,
        "current_sum_insured": 500000,
        "claimed_amount": 55000,
        "room_expense": 10000,
        "icu_expense": 0,
        "doctor_expense": 15000,
        "medicine_diagnostic_expense": 30000,
        "pre_hospitalization_expense": 0,
        "post_hospitalization_expense": 0,
        "ambulance_expense": 0,
        "pre_hospitalization_days_before": None,
        "post_hospitalization_days_after_discharge": None,
        "same_condition_confirmed": None,
        "documents": ["claim_form"],
        "evidence_context_present": True,
        "expense_timing_present": False,
        "prior_policy_present": False,
        "dataset_continuous_coverage_months": None,
        "additional_information": (
            "Hospital registration, minimum criteria, and medical necessity "
            "evidence are unavailable."
        ),
    },

    "CUS-005 — Experimental Treatment": {
        "case_id": "CUS-005",
        "policy_start_date": "2024-01-01",
        "claim_date": "2026-06-01",
        "hospitalization_start_date": "2026-06-01",
        "hospitalization_end_date": "2026-06-05",
        "diagnosis": "Cancer",
        "treatment": "Experimental cancer therapy",
        "domiciliary_treatment": False,
        "experimental": True,
        "hospital_name": "City Hospital",
        "hospital_registration": "REG-12345",
        "hospital_registered": True,
        "hospital_minimum_criteria_documented": True,
        "is_inpatient": True,
        "treatment_duration_hours": 96,
        "hospital_room_unavailable": False,
        "patient_cannot_be_moved": False,
        "medical_necessity_confirmed": True,
        "pre_existing_disease": False,
        "current_sum_insured": 500000,
        "claimed_amount": 135000,
        "room_expense": 20000,
        "icu_expense": 0,
        "doctor_expense": 40000,
        "medicine_diagnostic_expense": 75000,
        "pre_hospitalization_expense": 0,
        "post_hospitalization_expense": 0,
        "ambulance_expense": 0,
        "documents": [
            "claim_form",
            "hospital_bill",
            "discharge_summary",
        ],
        "evidence_context_present": True,
        "expense_timing_present": False,
        "prior_policy_present": False,
        "dataset_continuous_coverage_months": None,
        "additional_information": (
            "Treatment is explicitly marked as experimental."
        ),
    },
}


# =========================================================
# HELPERS
# =========================================================

def money(value: Any) -> str:
    if value is None:
        return "N/A"

    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def number_value(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def decision_info(decision: str):
    mapping = {
        "ADMISSIBLE": (
            "✅",
            "Claim is admissible.",
        ),
        "ADMISSIBLE_WITH_LIMITS": (
            "⚠️",
            "Claim is admissible subject to policy limits.",
        ),
        "PARTIALLY_ADMISSIBLE": (
            "⚠️",
            "Claim is partially admissible.",
        ),
        "NOT_ADMISSIBLE": (
            "❌",
            "Claim is not admissible under the evaluated policy rules.",
        ),
        "NEEDS_REVIEW": (
            "🔎",
            "Additional evidence is required before a final decision.",
        ),
    }

    return mapping.get(
        decision,
        ("ℹ️", "Decision returned by the policy engine."),
    )


def check_api() -> bool:
    try:
        response = requests.get(
            f"{API_URL}/health",
            timeout=5,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def analyze_claim(payload: dict) -> dict:
    response = requests.post(
        f"{API_URL}/analyze",
        json=payload,
        timeout=180,
    )

    if response.status_code != 200:
        try:
            detail = response.json()
        except Exception:
            detail = response.text

        raise RuntimeError(
            f"API returned HTTP {response.status_code}: {detail}"
        )

    return response.json()


def unique_citations(citations: list[dict]) -> list[dict]:
    """
    Remove exact duplicate citations while preserving order.
    """
    unique = []
    seen = set()

    for citation in citations:
        key = (
            citation.get("claim"),
            citation.get("source"),
            citation.get("page"),
            citation.get("section"),
            citation.get("chunk_id"),
        )

        if key not in seen:
            seen.add(key)
            unique.append(citation)

    return unique


def build_payload(values: dict) -> dict:
    return {
        "case_id": values["case_id"],
        "policy_start_date": values["policy_start_date"],
        "claim_date": values["claim_date"],
        "hospitalization_start_date": values[
            "hospitalization_start_date"
        ],
        "hospitalization_end_date": values[
            "hospitalization_end_date"
        ],
        "diagnosis": values["diagnosis"],
        "treatment": values["treatment"],
        "domiciliary_treatment": values[
            "domiciliary_treatment"
        ],
        "experimental": values["experimental"],
        "hospital_name": values["hospital_name"],
        "hospital_registration": values[
            "hospital_registration"
        ],
        "hospital_registered": values[
            "hospital_registered"
        ],
        "hospital_minimum_criteria_documented": values[
            "hospital_minimum_criteria_documented"
        ],
        "is_inpatient": values["is_inpatient"],
        "treatment_duration_hours": values[
            "treatment_duration_hours"
        ],
        "hospital_room_unavailable": values[
            "hospital_room_unavailable"
        ],
        "patient_cannot_be_moved": values[
            "patient_cannot_be_moved"
        ],
        "medical_necessity_confirmed": values[
            "medical_necessity_confirmed"
        ],
        "pre_existing_disease": values[
            "pre_existing_disease"
        ],
        "pre_existing_details": values[
            "pre_existing_details"
        ],
        "prior_insurer": values["prior_insurer"],
        "prior_policy_insurer_type": values[
            "prior_policy_insurer_type"
        ],
        "prior_coverage_years": values[
            "prior_coverage_years"
        ],
        "prior_policy_records_received": values[
            "prior_policy_records_received"
        ],
        "prior_sum_insured": values["prior_sum_insured"],
        "current_sum_insured": values[
            "current_sum_insured"
        ],
        "claimed_amount": values["claimed_amount"],
        "room_expense": values["room_expense"],
        "icu_expense": values["icu_expense"],
        "doctor_expense": values["doctor_expense"],
        "medicine_diagnostic_expense": values[
            "medicine_diagnostic_expense"
        ],
        "pre_hospitalization_expense": values[
            "pre_hospitalization_expense"
        ],
        "post_hospitalization_expense": values[
            "post_hospitalization_expense"
        ],
        "ambulance_expense": values[
            "ambulance_expense"
        ],
        "pre_hospitalization_days_before": values[
            "pre_hospitalization_days_before"
        ],
        "post_hospitalization_days_after_discharge": values[
            "post_hospitalization_days_after_discharge"
        ],
        "same_condition_confirmed": values[
            "same_condition_confirmed"
        ],
        "documents": values["documents"],
        "evidence_context_present": values[
            "evidence_context_present"
        ],
        "expense_timing_present": values[
            "expense_timing_present"
        ],
        "prior_policy_present": values[
            "prior_policy_present"
        ],
        "dataset_continuous_coverage_months": values[
            "dataset_continuous_coverage_months"
        ],
        "additional_information": values[
            "additional_information"
        ],
    }


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">'
    "🛡️ Policy-Aware Insurance Claim Decision Engine"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Multi-agent RAG system for policy-grounded claim decisions, "
    "deductions, citations, and evidence-aware abstention."
    "</div>",
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("System")

    st.write("**Backend:** FastAPI")
    st.write("**Orchestration:** LangGraph")
    st.write("**Retrieval:** Dense + Sparse + Reranking")
    st.write("**Policy:** Supplied insurance policy")

    st.divider()

    if check_api():
        st.success("API Connected")
    else:
        st.error("API Unavailable")

    st.divider()

    st.write("**Policy-Aware Claim Engine**")
    st.caption("Version 1.0.0")


# =========================================================
# DEMO CASE SELECTOR
# =========================================================

st.markdown("### 🧪 Demo Cases")

demo_case = st.selectbox(
    "Select a test case",
    list(DEMO_CASES.keys()),
)

selected_demo = DEMO_CASES[demo_case]

if selected_demo is not None:

    st.success(
        f"Demo case loaded: **{selected_demo['case_id']}**"
    )

    st.caption(
        "The form below is populated from the selected "
        "evaluation case. You can modify any field before analysis."
    )


# =========================================================
# DEFAULT VALUES
# =========================================================

defaults = selected_demo or {
    "case_id": "CUSTOM-001",
    "policy_start_date": "2024-01-01",
    "claim_date": "2026-06-01",
    "hospitalization_start_date": "2026-06-01",
    "hospitalization_end_date": "2026-06-03",
    "diagnosis": "Pneumonia",
    "treatment": "Inpatient hospitalization",
    "domiciliary_treatment": False,
    "experimental": False,
    "hospital_name": "City Hospital",
    "hospital_registration": "REG-12345",
    "hospital_registered": True,
    "hospital_minimum_criteria_documented": True,
    "is_inpatient": True,
    "treatment_duration_hours": 72.0,
    "hospital_room_unavailable": False,
    "patient_cannot_be_moved": False,
    "medical_necessity_confirmed": True,
    "pre_existing_disease": False,
    "pre_existing_details": None,
    "prior_insurer": None,
    "prior_policy_insurer_type": None,
    "prior_coverage_years": None,
    "prior_policy_records_received": False,
    "prior_sum_insured": None,
    "current_sum_insured": 500000.0,
    "claimed_amount": 100000.0,
    "room_expense": 10000.0,
    "icu_expense": 0.0,
    "doctor_expense": 20000.0,
    "medicine_diagnostic_expense": 30000.0,
    "pre_hospitalization_expense": 0.0,
    "post_hospitalization_expense": 0.0,
    "ambulance_expense": 0.0,
    "pre_hospitalization_days_before": None,
    "post_hospitalization_days_after_discharge": None,
    "same_condition_confirmed": None,
    "documents": [
        "claim_form",
        "hospital_bill",
        "discharge_summary",
    ],
    "evidence_context_present": True,
    "expense_timing_present": False,
    "prior_policy_present": False,
    "dataset_continuous_coverage_months": None,
    "additional_information": (
        "Complete claim and hospitalization evidence is available."
    ),
}


# =========================================================
# CLAIM FORM
# =========================================================

st.markdown("### 📋 Claim Information")

with st.form("claim_form"):

    col1, col2, col3 = st.columns(3)

    with col1:

        case_id = st.text_input(
            "Case ID",
            value=defaults["case_id"],
        )

        policy_start_date = st.date_input(
            "Policy Start Date",
            value=date.fromisoformat(
                defaults["policy_start_date"]
            ),
        )

        claim_date = st.date_input(
            "Claim Date",
            value=date.fromisoformat(
                defaults["claim_date"]
            ),
        )

        diagnosis = st.text_input(
            "Diagnosis",
            value=defaults["diagnosis"],
        )

    with col2:

        hospitalization_start_date = st.date_input(
            "Hospitalization Start Date",
            value=date.fromisoformat(
                defaults["hospitalization_start_date"]
            ),
        )

        hospitalization_end_date = st.date_input(
            "Hospitalization End Date",
            value=date.fromisoformat(
                defaults["hospitalization_end_date"]
            ),
        )

        treatment_duration_hours = st.number_input(
            "Treatment Duration (hours)",
            min_value=0.0,
            value=float(
                defaults["treatment_duration_hours"]
            ),
            step=1.0,
        )

        treatment = st.text_input(
            "Treatment",
            value=defaults["treatment"],
        )

    with col3:

        current_sum_insured = st.number_input(
            "Basic Sum Insured",
            min_value=0.0,
            value=float(
                defaults["current_sum_insured"]
            ),
            step=10000.0,
        )

        claimed_amount = st.number_input(
            "Claimed Amount",
            min_value=0.0,
            value=float(
                defaults["claimed_amount"]
            ),
            step=1000.0,
        )

        hospital_name = st.text_input(
            "Hospital Name",
            value=defaults["hospital_name"],
        )

        hospital_registration = st.text_input(
            "Hospital Registration",
            value=defaults["hospital_registration"] or "",
        )

    st.divider()

    st.markdown("### 🏥 Hospital & Treatment")

    h1, h2, h3, h4 = st.columns(4)

    with h1:
        is_inpatient = st.checkbox(
            "Inpatient",
            value=bool(defaults["is_inpatient"]),
        )

    with h2:
        hospital_registered = st.checkbox(
            "Hospital Registered",
            value=bool(
                defaults["hospital_registered"]
            ),
        )

    with h3:
        hospital_minimum_criteria_documented = st.checkbox(
            "Minimum Criteria Documented",
            value=bool(
                defaults[
                    "hospital_minimum_criteria_documented"
                ]
            ),
        )

    with h4:
        medical_necessity_confirmed = st.checkbox(
            "Medical Necessity Confirmed",
            value=bool(
                defaults["medical_necessity_confirmed"]
            ),
        )

    h5, h6, h7, h8 = st.columns(4)

    with h5:
        domiciliary_treatment = st.checkbox(
            "Domiciliary Treatment",
            value=bool(
                defaults["domiciliary_treatment"]
            ),
        )

    with h6:
        experimental = st.checkbox(
            "Experimental Treatment",
            value=bool(
                defaults["experimental"]
            ),
        )

    with h7:
        hospital_room_unavailable = st.checkbox(
            "Hospital Room Unavailable",
            value=bool(
                defaults["hospital_room_unavailable"]
            ),
        )

    with h8:
        patient_cannot_be_moved = st.checkbox(
            "Patient Cannot Be Moved",
            value=bool(
                defaults["patient_cannot_be_moved"]
            ),
        )

    st.divider()

    st.markdown("### 📄 Pre-existing / Prior Coverage")

    p1, p2, p3 = st.columns(3)

    with p1:

        pre_existing_disease = st.checkbox(
            "Pre-existing Disease",
            value=bool(
                defaults["pre_existing_disease"]
            ),
        )

        prior_policy_present = st.checkbox(
            "Prior Policy Present",
            value=bool(
                defaults["prior_policy_present"]
            ),
        )

    with p2:

        prior_coverage_years = st.number_input(
            "Prior Coverage (years)",
            min_value=0.0,
            value=float(
                defaults["prior_coverage_years"] or 0
            ),
            step=0.5,
        )

        prior_policy_records_received = st.checkbox(
            "Prior Policy Records Received",
            value=bool(
                defaults[
                    "prior_policy_records_received"
                ]
            ),
        )

    with p3:

        prior_sum_insured = st.number_input(
            "Prior Sum Insured",
            min_value=0.0,
            value=float(
                defaults["prior_sum_insured"] or 0
            ),
            step=10000.0,
        )

        dataset_continuous_coverage_months = st.number_input(
            "Continuous Coverage (months)",
            min_value=0.0,
            value=float(
                defaults[
                    "dataset_continuous_coverage_months"
                ] or 0
            ),
            step=1.0,
        )

    st.divider()

    st.markdown("### 💰 Expense Details")

    e1, e2, e3 = st.columns(3)

    with e1:

        room_expense = st.number_input(
            "Room Expense",
            min_value=0.0,
            value=float(
                defaults["room_expense"]
            ),
            step=1000.0,
        )

        icu_expense = st.number_input(
            "ICU Expense",
            min_value=0.0,
            value=float(
                defaults["icu_expense"]
            ),
            step=1000.0,
        )

        doctor_expense = st.number_input(
            "Doctor Expense",
            min_value=0.0,
            value=float(
                defaults["doctor_expense"]
            ),
            step=1000.0,
        )

    with e2:

        medicine_diagnostic_expense = st.number_input(
            "Medicines / Diagnostics",
            min_value=0.0,
            value=float(
                defaults[
                    "medicine_diagnostic_expense"
                ]
            ),
            step=1000.0,
        )

        ambulance_expense = st.number_input(
            "Ambulance Expense",
            min_value=0.0,
            value=float(
                defaults["ambulance_expense"]
            ),
            step=500.0,
        )

        pre_hospitalization_expense = st.number_input(
            "Pre-hospitalization Expense",
            min_value=0.0,
            value=float(
                defaults[
                    "pre_hospitalization_expense"
                ]
            ),
            step=1000.0,
        )

    with e3:

        post_hospitalization_expense = st.number_input(
            "Post-hospitalization Expense",
            min_value=0.0,
            value=float(
                defaults[
                    "post_hospitalization_expense"
                ]
            ),
            step=1000.0,
        )

        pre_hospitalization_days_before = st.number_input(
            "Pre-hospitalization Days",
            min_value=0.0,
            value=float(
                defaults[
                    "pre_hospitalization_days_before"
                ] or 0
            ),
            step=1.0,
        )

        post_hospitalization_days_after_discharge = (
            st.number_input(
                "Post-hospitalization Days",
                min_value=0.0,
                value=float(
                    defaults[
                        "post_hospitalization_days_after_discharge"
                    ] or 0
                ),
                step=1.0,
            )
        )

    st.divider()

    evidence_context_present = st.checkbox(
        "Sufficient evidence context is available",
        value=bool(
            defaults["evidence_context_present"]
        ),
    )

    expense_timing_present = st.checkbox(
        "Expense timing evidence is available",
        value=bool(
            defaults["expense_timing_present"]
        ),
    )

    same_condition_confirmed = st.checkbox(
        "Pre/Post expenses relate to same condition",
        value=(
            True
            if defaults["same_condition_confirmed"] is True
            else False
        ),
    )

    additional_information = st.text_area(
        "Additional Information",
        value=defaults[
            "additional_information"
        ],
    )

    submitted = st.form_submit_button(
        "🔍 Analyze Claim",
        use_container_width=True,
        type="primary",
    )


# =========================================================
# SUBMIT CLAIM
# =========================================================

if submitted:

    payload = build_payload(
        {
            "case_id": case_id,
            "policy_start_date": str(
                policy_start_date
            ),
            "claim_date": str(claim_date),
            "hospitalization_start_date": str(
                hospitalization_start_date
            ),
            "hospitalization_end_date": str(
                hospitalization_end_date
            ),
            "diagnosis": diagnosis,
            "treatment": treatment,
            "domiciliary_treatment":
                domiciliary_treatment,
            "experimental": experimental,
            "hospital_name": hospital_name,
            "hospital_registration":
                hospital_registration or None,
            "hospital_registered":
                hospital_registered,
            "hospital_minimum_criteria_documented":
                hospital_minimum_criteria_documented,
            "is_inpatient": is_inpatient,
            "treatment_duration_hours":
                treatment_duration_hours,
            "hospital_room_unavailable":
                hospital_room_unavailable,
            "patient_cannot_be_moved":
                patient_cannot_be_moved,
            "medical_necessity_confirmed":
                medical_necessity_confirmed,
            "pre_existing_disease":
                pre_existing_disease,
            "pre_existing_details": None,
            "prior_insurer": None,
            "prior_policy_insurer_type": None,
            "prior_coverage_years":
                prior_coverage_years
                if prior_coverage_years > 0
                else None,
            "prior_policy_records_received":
                prior_policy_records_received,
            "prior_sum_insured":
                prior_sum_insured
                if prior_sum_insured > 0
                else None,
            "current_sum_insured":
                current_sum_insured,
            "claimed_amount":
                claimed_amount,
            "room_expense":
                room_expense,
            "icu_expense":
                icu_expense,
            "doctor_expense":
                doctor_expense,
            "medicine_diagnostic_expense":
                medicine_diagnostic_expense,
            "pre_hospitalization_expense":
                pre_hospitalization_expense,
            "post_hospitalization_expense":
                post_hospitalization_expense,
            "ambulance_expense":
                ambulance_expense,
            "pre_hospitalization_days_before":
                pre_hospitalization_days_before
                if pre_hospitalization_days_before > 0
                else None,
            "post_hospitalization_days_after_discharge":
                post_hospitalization_days_after_discharge
                if post_hospitalization_days_after_discharge > 0
                else None,
            "same_condition_confirmed":
                same_condition_confirmed,
            "documents": defaults.get(
                "documents",
                [
                    "claim_form",
                    "hospital_bill",
                    "discharge_summary",
                ],
            ),
            "evidence_context_present":
                evidence_context_present,
            "expense_timing_present":
                expense_timing_present,
            "prior_policy_present":
                prior_policy_present,
            "dataset_continuous_coverage_months":
                dataset_continuous_coverage_months
                if dataset_continuous_coverage_months > 0
                else None,
            "additional_information":
                additional_information,
        }
    )

    with st.spinner(
        "Running multi-agent policy analysis..."
    ):
        try:

            result = analyze_claim(payload)

            st.session_state["result"] = result

            st.session_state["last_case_id"] = case_id

        except Exception as exc:

            st.error(
                f"Claim analysis failed: {exc}"
            )


# =========================================================
# RESULTS
# =========================================================

result = st.session_state.get("result")

if result:

    st.divider()

    decision = result.get(
        "decision",
        "UNKNOWN",
    )

    confidence = number_value(
        result.get("confidence"),
        0.0,
    )

    icon, message = decision_info(
        decision
    )

    st.markdown(
        f"""
        <div class="decision-box">
            <h2>{icon} {decision}</h2>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------

    deductions = result.get(
        "deductions",
        [],
    ) or []

    total_deductions = sum(
        number_value(
            item.get("deduction")
        )
        for item in deductions
    )

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "Decision",
            decision,
        )

    with m2:
        st.metric(
            "Confidence",
            f"{confidence:.0%}",
        )

    with m3:
        st.metric(
            "Payable Amount",
            money(
                result.get(
                    "payable_amount"
                )
            ),
        )

    with m4:
        st.metric(
            "Total Deductions",
            money(total_deductions),
        )

    # -----------------------------------------------------
    # Findings
    # -----------------------------------------------------

    st.markdown(
        "### 🔎 Key Findings"
    )

    findings = result.get(
        "key_findings",
        [],
    ) or []

    if findings:

        for finding in findings:
            st.write(f"• {finding}")

    else:
        st.info(
            "No key findings returned."
        )

    # -----------------------------------------------------
    # Limits
    # -----------------------------------------------------

    st.markdown(
        "### 📏 Applicable Policy Limits"
    )

    limits = result.get(
        "applicable_limits",
        [],
    ) or []

    if limits:

        for limit in limits:
            st.write(f"• {limit}")

    else:
        st.info(
            "No applicable limits returned."
        )

    # -----------------------------------------------------
    # Deductions
    # -----------------------------------------------------

    st.markdown(
        "### 💰 Deductions"
    )

    if deductions:

        deduction_rows = []

        for item in deductions:

            deduction_rows.append(
                {
                    "Category":
                        item.get(
                            "category",
                            "",
                        ),
                    "Claimed":
                        money(
                            item.get(
                                "claimed"
                            )
                        ),
                    "Allowed":
                        money(
                            item.get(
                                "allowed"
                            )
                        ),
                    "Deduction":
                        money(
                            item.get(
                                "deduction"
                            )
                        ),
                    "Reason":
                        item.get(
                            "reason",
                            "",
                        ),
                }
            )

        st.dataframe(
            deduction_rows,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.success(
            "No deductions."
        )

    # -----------------------------------------------------
    # Evidence
    # -----------------------------------------------------

    st.markdown(
        "### 📂 Evidence Status"
    )

    missing = result.get(
        "missing_evidence",
        [],
    ) or []

    if missing:

        st.warning(
            "Additional evidence is required."
        )

        for item in missing:
            st.write(f"• {item}")

    else:

        st.success(
            "No missing evidence identified."
        )

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    validation = result.get(
        "validation",
        {},
    ) or {}

    validation_status = validation.get(
        "status",
        "UNKNOWN",
    )

    if validation_status == "VALID":

        st.success(
            f"Validation: {validation_status}"
        )

    elif validation_status == "VALID_ABSTENTION":

        st.warning(
            f"Validation: {validation_status}"
        )

    else:

        st.error(
            f"Validation: {validation_status}"
        )

    unsupported_claims = validation.get(
        "unsupported_claims",
        [],
    ) or []

    if unsupported_claims:

        st.warning(
            "Unsupported claims detected:"
        )

        for claim in unsupported_claims:
            st.write(f"• {claim}")

    # -----------------------------------------------------
    # Citations
    # -----------------------------------------------------

    st.markdown(
        "### 📚 Policy Citations"
    )

    citations = unique_citations(
        result.get(
            "citations",
            [],
        ) or []
    )

    if citations:

        st.caption(
            f"{len(citations)} unique policy citations"
        )

        for index, citation in enumerate(
            citations,
            start=1,
        ):

            claim = citation.get(
                "claim",
                "Policy evidence",
            )

            with st.expander(
                f"Citation {index}: {claim}"
            ):

                c1, c2 = st.columns(2)

                with c1:

                    st.write(
                        "**Source**"
                    )

                    st.code(
                        citation.get(
                            "source",
                            "",
                        )
                    )

                    st.write(
                        f"**Page:** "
                        f"{citation.get('page', '')}"
                    )

                with c2:

                    st.write(
                        f"**Section:** "
                        f"{citation.get('section', '')}"
                    )

                    st.write(
                        f"**Chunk ID:** "
                        f"{citation.get('chunk_id', '')}"
                    )

    else:

        st.info(
            "No policy citations returned."
        )

    # -----------------------------------------------------
    # Agent Trace
    # -----------------------------------------------------

    st.markdown(
        "### 🤖 Agent Trace"
    )

    trace = result.get(
        "trace",
        [],
    ) or []

    if trace:

        trace_rows = []

        for step in trace:

            trace_rows.append(
                {
                    "Agent":
                        step.get(
                            "agent",
                            "",
                        ),
                    "Action":
                        step.get(
                            "action",
                            "",
                        ),
                    "Retrieval Count":
                        step.get(
                            "retrieval_count",
                            "",
                        ),
                    "Validation":
                        step.get(
                            "validation_status",
                            "",
                        ),
                    "Elapsed (ms)":
                        step.get(
                            "elapsed_ms",
                            "",
                        ),
                }
            )

        st.dataframe(
            trace_rows,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No agent trace returned."
        )

    # -----------------------------------------------------
    # Raw JSON
    # -----------------------------------------------------

    st.markdown(
        "### 🧾 Raw Decision JSON"
    )

    with st.expander(
        "View machine-readable output"
    ):

        st.json(result)

        download_case_id = st.session_state.get(
            "last_case_id",
            result.get(
                "case_id",
                "claim",
            ),
        )

        st.download_button(
            label="⬇️ Download JSON",
            data=json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            ),
            file_name=(
                f"{download_case_id}_decision.json"
            ),
            mime="application/json",
        )