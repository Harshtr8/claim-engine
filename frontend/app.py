import json
from datetime import date
from typing import Any, Optional

import requests
import streamlit as st


# ============================================================
# CONFIG
# ============================================================

API_URL = "https://aptino-claim-engine-api-8304.onrender.com"

st.set_page_config(
    page_title="Policy-Aware Claim Engine",
    page_icon="🛡️",
    layout="wide",
)


# ============================================================
# DEMO CASES
# ============================================================

DEMO_CASES = {
    "Manual Input": None,

    "CUS-001": {
        "case_id": "CUS-001",
        "policy_start_date": "2024-01-01",
        "claim_date": "2026-06-01",
        "hospitalization_start_date": "2026-06-01",
        "hospitalization_end_date": "2026-06-04",
        "diagnosis": "Appendicitis",
        "treatment": "Appendectomy",
        "basic_sum_insured": 500000,
        "claimed_amount": 144800,
        "hospital_name": "City Hospital",
        "hospital_registration": "REG-12345",
        "hospital_registered": True,
        "hospital_minimum_criteria_documented": True,
        "is_inpatient": True,
        "treatment_duration_hours": 72,
        "domiciliary_treatment": False,
        "experimental": False,
        "hospital_room_unavailable": False,
        "patient_cannot_be_moved": False,
        "medical_necessity_confirmed": True,
        "pre_existing_disease": False,
        "prior_policy_present": False,
        "prior_coverage_years": None,
        "prior_policy_records_received": None,
        "prior_sum_insured": None,
        "continuous_coverage_months": None,
        "room_expense": 12000,
        "icu_expense": 0,
        "doctor_expense": 40000,
        "medicine_diagnostic_expense": 80000,
        "ambulance_expense": 800,
        "pre_hospitalization_expense": 5000,
        "post_hospitalization_expense": 7000,
        "pre_hospitalization_days_before": 20,
        "post_hospitalization_days_after_discharge": 30,
        "same_condition_confirmed": True,
        "evidence_context_present": True,
        "expense_timing_present": True,
        "additional_information": "Complete supporting documents available.",
    },

    "CUS-002": {
        "case_id": "CUS-002",
        "policy_start_date": "2024-01-01",
        "claim_date": "2026-06-01",
        "hospitalization_start_date": "2026-06-01",
        "hospitalization_end_date": "2026-06-05",
        "diagnosis": "Pneumonia",
        "treatment": "Inpatient treatment",
        "basic_sum_insured": 500000,
        "claimed_amount": 541500,
        "hospital_name": "Metro Care Hospital",
        "hospital_registration": "REG-67890",
        "hospital_registered": True,
        "hospital_minimum_criteria_documented": True,
        "is_inpatient": True,
        "treatment_duration_hours": 96,
        "domiciliary_treatment": False,
        "experimental": False,
        "hospital_room_unavailable": False,
        "patient_cannot_be_moved": False,
        "medical_necessity_confirmed": True,
        "pre_existing_disease": False,
        "prior_policy_present": False,
        "prior_coverage_years": None,
        "prior_policy_records_received": None,
        "prior_sum_insured": None,
        "continuous_coverage_months": None,
        "room_expense": 30000,
        "icu_expense": 60000,
        "doctor_expense": 200000,
        "medicine_diagnostic_expense": 250000,
        "ambulance_expense": 1500,
        "pre_hospitalization_expense": 0,
        "post_hospitalization_expense": 0,
        "pre_hospitalization_days_before": None,
        "post_hospitalization_days_after_discharge": None,
        "same_condition_confirmed": None,
        "evidence_context_present": True,
        "expense_timing_present": False,
        "additional_information": "Complete hospital and expense evidence available.",
    },

    "CUS-003": {
        "case_id": "CUS-003",
        "policy_start_date": "2024-01-01",
        "claim_date": "2026-06-01",
        "hospitalization_start_date": "2026-06-01",
        "hospitalization_end_date": "2026-06-04",
        "diagnosis": "Diabetes Mellitus",
        "treatment": "Inpatient treatment",
        "basic_sum_insured": 500000,
        "claimed_amount": 55000,
        "hospital_name": "General Hospital",
        "hospital_registration": "REG-11111",
        "hospital_registered": True,
        "hospital_minimum_criteria_documented": True,
        "is_inpatient": True,
        "treatment_duration_hours": 72,
        "domiciliary_treatment": False,
        "experimental": False,
        "hospital_room_unavailable": False,
        "patient_cannot_be_moved": False,
        "medical_necessity_confirmed": True,
        "pre_existing_disease": True,
        "prior_policy_present": False,
        "prior_coverage_years": None,
        "prior_policy_records_received": None,
        "prior_sum_insured": None,
        "continuous_coverage_months": None,
        "room_expense": 10000,
        "icu_expense": 0,
        "doctor_expense": 15000,
        "medicine_diagnostic_expense": 30000,
        "ambulance_expense": 0,
        "pre_hospitalization_expense": 0,
        "post_hospitalization_expense": 0,
        "pre_hospitalization_days_before": None,
        "post_hospitalization_days_after_discharge": None,
        "same_condition_confirmed": None,
        "evidence_context_present": False,
        "expense_timing_present": False,
        "additional_information": "Pre-existing disease indicated in claim information.",
    },

    # --------------------------------------------------------
    # CUS-004
    # --------------------------------------------------------
    # Deliberately incomplete evidence.
    #
    # IMPORTANT:
    # None = information was NOT PROVIDED.
    # It must NOT become False.
    #
    "CUS-004": {
        "case_id": "CUS-004",
        "policy_start_date": "2024-01-01",
        "claim_date": "2026-06-01",
        "hospitalization_start_date": "2026-06-01",
        "hospitalization_end_date": "2026-06-04",
        "diagnosis": "Gallbladder Infection",
        "treatment": "Inpatient treatment",
        "basic_sum_insured": 500000,
        "claimed_amount": 55000,
        "hospital_name": "Local Hospital",
        "hospital_registration": None,

        # DO NOT CHANGE THESE TO FALSE.
        "hospital_registered": None,
        "hospital_minimum_criteria_documented": None,
        "medical_necessity_confirmed": None,

        "is_inpatient": True,
        "treatment_duration_hours": 72,
        "domiciliary_treatment": False,
        "experimental": False,
        "hospital_room_unavailable": False,
        "patient_cannot_be_moved": False,
        "pre_existing_disease": False,
        "prior_policy_present": False,
        "prior_coverage_years": None,
        "prior_policy_records_received": None,
        "prior_sum_insured": None,
        "continuous_coverage_months": None,
        "room_expense": 10000,
        "icu_expense": 0,
        "doctor_expense": 15000,
        "medicine_diagnostic_expense": 30000,
        "ambulance_expense": 0,
        "pre_hospitalization_expense": 0,
        "post_hospitalization_expense": 0,
        "pre_hospitalization_days_before": None,
        "post_hospitalization_days_after_discharge": None,
        "same_condition_confirmed": None,
        "evidence_context_present": False,
        "expense_timing_present": False,
        "additional_information": (
            "Only claim form is available. "
            "Hospital registration, minimum criteria, and "
            "medical necessity evidence were not provided."
        ),
    },

    # --------------------------------------------------------
    # CUS-005
    # --------------------------------------------------------
    # Explicitly complete hospital evidence + experimental
    # treatment.
    #
    # Therefore:
    # NOT_ADMISSIBLE
    # missing_evidence = []
    #
    "CUS-005": {
        "case_id": "CUS-005",
        "policy_start_date": "2024-01-01",
        "claim_date": "2026-06-01",
        "hospitalization_start_date": "2026-06-01",
        "hospitalization_end_date": "2026-06-05",
        "diagnosis": "Cancer",
        "treatment": "Experimental cancer therapy",
        "basic_sum_insured": 500000,
        "claimed_amount": 135000,
        "hospital_name": "Advanced Cancer Institute",
        "hospital_registration": "REG-99999",

        # Explicit evidence is available.
        "hospital_registered": True,
        "hospital_minimum_criteria_documented": True,
        "medical_necessity_confirmed": True,

        "is_inpatient": True,
        "treatment_duration_hours": 96,
        "domiciliary_treatment": False,

        # Explicit exclusion trigger.
        "experimental": True,

        "hospital_room_unavailable": False,
        "patient_cannot_be_moved": False,

        "pre_existing_disease": False,
        "prior_policy_present": False,
        "prior_coverage_years": None,
        "prior_policy_records_received": None,
        "prior_sum_insured": None,
        "continuous_coverage_months": None,

        "room_expense": 20000,
        "icu_expense": 0,
        "doctor_expense": 50000,
        "medicine_diagnostic_expense": 65000,
        "ambulance_expense": 0,
        "pre_hospitalization_expense": 0,
        "post_hospitalization_expense": 0,
        "pre_hospitalization_days_before": None,
        "post_hospitalization_days_after_discharge": None,
        "same_condition_confirmed": None,

        # Evidence is explicitly available.
        "evidence_context_present": True,
        "expense_timing_present": False,

        "additional_information": (
            "Hospital evidence is available. "
            "Treatment is explicitly documented as experimental."
        ),
    },
}


# ============================================================
# MANUAL DEFAULTS
# ============================================================

MANUAL_DEFAULTS = {
    "case_id": "MANUAL-001",
    "policy_start_date": "2024-01-01",
    "claim_date": "2026-06-01",
    "hospitalization_start_date": "2026-06-01",
    "hospitalization_end_date": "2026-06-03",
    "diagnosis": "",
    "treatment": "",
    "basic_sum_insured": 500000,
    "claimed_amount": 0,
    "hospital_name": "",
    "hospital_registration": "",
    "hospital_registered": None,
    "hospital_minimum_criteria_documented": None,
    "is_inpatient": True,
    "treatment_duration_hours": 48,
    "domiciliary_treatment": False,
    "experimental": False,
    "hospital_room_unavailable": False,
    "patient_cannot_be_moved": False,
    "medical_necessity_confirmed": None,
    "pre_existing_disease": False,
    "prior_policy_present": False,
    "prior_coverage_years": None,
    "prior_policy_records_received": None,
    "prior_sum_insured": None,
    "continuous_coverage_months": None,
    "room_expense": 0,
    "icu_expense": 0,
    "doctor_expense": 0,
    "medicine_diagnostic_expense": 0,
    "ambulance_expense": 0,
    "pre_hospitalization_expense": 0,
    "post_hospitalization_expense": 0,
    "pre_hospitalization_days_before": None,
    "post_hospitalization_days_after_discharge": None,
    "same_condition_confirmed": None,
    "evidence_context_present": False,
    "expense_timing_present": False,
    "additional_information": "",
}


# ============================================================
# HELPERS
# ============================================================

def money(value: Any) -> str:
    if value is None:
        return "—"

    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def numeric(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_date(value: Any) -> date:
    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value))


def tri_state(
    label: str,
    value: Optional[bool],
    key: str,
    help_text: Optional[str] = None,
) -> Optional[bool]:
    """
    Three possible values:

    Not provided -> None
    Yes          -> True
    No           -> False
    """

    options = [
        "Not provided",
        "Yes",
        "No",
    ]

    if value is True:
        default_index = 1
    elif value is False:
        default_index = 2
    else:
        default_index = 0

    selected = st.selectbox(
        label,
        options,
        index=default_index,
        key=key,
        help=help_text,
    )

    if selected == "Yes":
        return True

    if selected == "No":
        return False

    return None


def api_available() -> bool:
    try:
        response = requests.get(
            f"{API_URL}/health",
            timeout=3,
        )
        return response.status_code == 200

    except requests.RequestException:
        return False


def analyze_claim(payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        f"{API_URL}/analyze",
        json=payload,
        timeout=180,
    )

    if response.status_code != 200:
        try:
            error = response.json()
        except Exception:
            error = response.text

        raise RuntimeError(
            f"API returned HTTP {response.status_code}: {error}"
        )

    return response.json()


def unique_citations(
    citations: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    seen = set()
    output = []

    for citation in citations or []:

        key = (
            citation.get("claim"),
            citation.get("source"),
            citation.get("page"),
            citation.get("section"),
            citation.get("chunk_id"),
        )

        if key not in seen:
            seen.add(key)
            output.append(citation)

    return output


def decision_info(decision: str):
    mapping = {
        "ADMISSIBLE": (
            "✅",
            "Claim is admissible under the evaluated policy rules.",
        ),
        "ADMISSIBLE_WITH_LIMITS": (
            "⚠️",
            "Claim is admissible subject to policy limits.",
        ),
        "PARTIALLY_ADMISSIBLE": (
            "⚠️",
            "Claim is partially admissible subject to the evaluated policy rules.",
        ),
        "NOT_ADMISSIBLE": (
            "❌",
            "Claim is not admissible under the evaluated policy rules.",
        ),
        "NEEDS_REVIEW": (
            "🔍",
            "Additional evidence is required before a final decision can be made.",
        ),
    }

    return mapping.get(
        decision,
        ("ℹ️", "Decision generated by the claim engine."),
    )


# ============================================================
# HEADER
# ============================================================

st.title(
    "🛡️ Policy-Aware Insurance Claim Decision Engine"
)

st.caption(
    "Multi-agent RAG system for policy-grounded claim decisions, "
    "deductions, citations, and evidence-aware abstention."
)


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**Backend**")
    st.write("FastAPI")

with col2:
    st.markdown("**Orchestration**")
    st.write("LangGraph")

with col3:
    st.markdown("**Retrieval**")
    st.write("Dense + Sparse + Reranking")

with col4:
    st.markdown("**Policy**")
    st.write("Supplied insurance policy")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("System")

    if api_available():
        st.success("API Connected")
    else:
        st.error("API Disconnected")

    st.divider()

    st.markdown("### Backend")
    st.code(API_URL)

    st.markdown("### Endpoints")
    st.write("GET `/health`")
    st.write("POST `/analyze`")

    st.divider()

    st.caption("Policy-Aware Claim Engine")
    st.caption("Version 1.0.0")


# ============================================================
# DEMO CASE SELECTOR
# ============================================================

st.header("🧪 Demo Cases")

selected_name = st.selectbox(
    "Select a test case",
    list(DEMO_CASES.keys()),
)

selected_demo = DEMO_CASES[selected_name]

if selected_demo is not None:

    st.success(
        f"Demo case loaded: **{selected_demo['case_id']}**"
    )

    st.caption(
        "The form below is populated from the selected evaluation case. "
        "You can modify any field before analysis."
    )

defaults = (
    selected_demo
    if selected_demo is not None
    else MANUAL_DEFAULTS
)


# ============================================================
# CLAIM INFORMATION
# ============================================================

st.header("📋 Claim Information")

col1, col2, col3 = st.columns(3)

with col1:
    case_id = st.text_input(
        "Case ID",
        value=str(defaults.get("case_id", "")),
    )

with col2:
    policy_start_date = st.date_input(
        "Policy Start Date",
        value=safe_date(
            defaults.get(
                "policy_start_date",
                "2024-01-01",
            )
        ),
    )

with col3:
    claim_date = st.date_input(
        "Claim Date",
        value=safe_date(
            defaults.get(
                "claim_date",
                "2026-06-01",
            )
        ),
    )


col1, col2 = st.columns(2)

with col1:
    diagnosis = st.text_input(
        "Diagnosis",
        value=str(
            defaults.get(
                "diagnosis",
                "",
            )
            or ""
        ),
    )

with col2:
    treatment = st.text_input(
        "Treatment",
        value=str(
            defaults.get(
                "treatment",
                "",
            )
            or ""
        ),
    )


col1, col2, col3 = st.columns(3)

with col1:
    hospitalization_start_date = st.date_input(
        "Hospitalization Start Date",
        value=safe_date(
            defaults.get(
                "hospitalization_start_date",
                defaults.get(
                    "claim_date",
                    "2026-06-01",
                ),
            )
        ),
    )

with col2:
    hospitalization_end_date = st.date_input(
        "Hospitalization End Date",
        value=safe_date(
            defaults.get(
                "hospitalization_end_date",
                defaults.get(
                    "claim_date",
                    "2026-06-01",
                ),
            )
        ),
    )

with col3:
    treatment_duration_hours = st.number_input(
        "Treatment Duration (hours)",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "treatment_duration_hours"
            ),
            0.0,
        ),
        step=1.0,
    )


col1, col2, col3 = st.columns(3)

with col1:
    basic_sum_insured = st.number_input(
        "Basic Sum Insured",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "basic_sum_insured"
            ),
            500000.0,
        ),
        step=1000.0,
    )

with col2:
    claimed_amount = st.number_input(
        "Claimed Amount",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "claimed_amount"
            ),
            0.0,
        ),
        step=1000.0,
    )

with col3:
    is_inpatient = st.checkbox(
        "Inpatient",
        value=bool(
            defaults.get(
                "is_inpatient",
                True,
            )
        ),
    )


col1, col2 = st.columns(2)

with col1:
    hospital_name = st.text_input(
        "Hospital Name",
        value=str(
            defaults.get(
                "hospital_name",
                "",
            )
            or ""
        ),
    )

with col2:
    hospital_registration = st.text_input(
        "Hospital Registration",
        value=str(
            defaults.get(
                "hospital_registration",
                "",
            )
            or ""
        ),
    )


# ============================================================
# HOSPITAL & TREATMENT
# ============================================================

st.header("🏥 Hospital & Treatment")

col1, col2, col3 = st.columns(3)

with col1:
    hospital_registered = tri_state(
        "Hospital Registered",
        defaults.get(
            "hospital_registered"
        ),
        key=f"hospital_registered_{selected_name}",
    )

with col2:
    hospital_minimum_criteria_documented = tri_state(
        "Minimum Criteria Documented",
        defaults.get(
            "hospital_minimum_criteria_documented"
        ),
        key=f"hospital_criteria_{selected_name}",
    )

with col3:
    medical_necessity_confirmed = tri_state(
        "Medical Necessity Confirmed",
        defaults.get(
            "medical_necessity_confirmed"
        ),
        key=f"medical_necessity_{selected_name}",
    )


col1, col2, col3, col4 = st.columns(4)

with col1:
    domiciliary_treatment = st.checkbox(
        "Domiciliary Treatment",
        value=bool(
            defaults.get(
                "domiciliary_treatment",
                False,
            )
        ),
        key=f"domiciliary_{selected_name}",
    )

with col2:
    experimental = st.checkbox(
        "Experimental Treatment",
        value=bool(
            defaults.get(
                "experimental",
                False,
            )
        ),
        key=f"experimental_{selected_name}",
    )

with col3:
    hospital_room_unavailable = st.checkbox(
        "Hospital Room Unavailable",
        value=bool(
            defaults.get(
                "hospital_room_unavailable",
                False,
            )
        ),
        key=f"room_unavailable_{selected_name}",
    )

with col4:
    patient_cannot_be_moved = st.checkbox(
        "Patient Cannot Be Moved",
        value=bool(
            defaults.get(
                "patient_cannot_be_moved",
                False,
            )
        ),
        key=f"cannot_move_{selected_name}",
    )


# ============================================================
# PRIOR COVERAGE
# ============================================================

st.header("📄 Pre-existing / Prior Coverage")

col1, col2, col3 = st.columns(3)

with col1:
    pre_existing_disease = st.checkbox(
        "Pre-existing Disease",
        value=bool(
            defaults.get(
                "pre_existing_disease",
                False,
            )
        ),
        key=f"pre_existing_{selected_name}",
    )

with col2:
    prior_policy_present = st.checkbox(
        "Prior Policy Present",
        value=bool(
            defaults.get(
                "prior_policy_present",
                False,
            )
        ),
        key=f"prior_policy_{selected_name}",
    )

with col3:
    prior_coverage_years = st.number_input(
        "Prior Coverage (years)",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "prior_coverage_years"
            ),
            0.0,
        ),
        step=0.5,
        key=f"prior_years_{selected_name}",
    )


col1, col2, col3 = st.columns(3)

with col1:
    prior_policy_records_received = tri_state(
        "Prior Policy Records Received",
        defaults.get(
            "prior_policy_records_received"
        ),
        key=f"prior_records_{selected_name}",
    )

with col2:
    prior_sum_insured = st.number_input(
        "Prior Sum Insured",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "prior_sum_insured"
            ),
            0.0,
        ),
        step=1000.0,
        key=f"prior_si_{selected_name}",
    )

with col3:
    continuous_coverage_months = st.number_input(
        "Continuous Coverage (months)",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "continuous_coverage_months"
            ),
            0.0,
        ),
        step=1.0,
        key=f"continuous_months_{selected_name}",
    )


# ============================================================
# EXPENSES
# ============================================================

st.header("💰 Expense Details")

col1, col2, col3, col4 = st.columns(4)

with col1:
    room_expense = st.number_input(
        "Room Expense",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "room_expense"
            ),
            0.0,
        ),
        step=1000.0,
        key=f"room_expense_{selected_name}",
    )

with col2:
    icu_expense = st.number_input(
        "ICU Expense",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "icu_expense"
            ),
            0.0,
        ),
        step=1000.0,
        key=f"icu_expense_{selected_name}",
    )

with col3:
    doctor_expense = st.number_input(
        "Doctor Expense",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "doctor_expense"
            ),
            0.0,
        ),
        step=1000.0,
        key=f"doctor_expense_{selected_name}",
    )

with col4:
    medicine_diagnostic_expense = st.number_input(
        "Medicines / Diagnostics",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "medicine_diagnostic_expense"
            ),
            0.0,
        ),
        step=1000.0,
        key=f"medicine_expense_{selected_name}",
    )


col1, col2, col3, col4 = st.columns(4)

with col1:
    ambulance_expense = st.number_input(
        "Ambulance Expense",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "ambulance_expense"
            ),
            0.0,
        ),
        step=100.0,
        key=f"ambulance_{selected_name}",
    )

with col2:
    pre_hospitalization_expense = st.number_input(
        "Pre-hospitalization Expense",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "pre_hospitalization_expense"
            ),
            0.0,
        ),
        step=1000.0,
        key=f"pre_expense_{selected_name}",
    )

with col3:
    post_hospitalization_expense = st.number_input(
        "Post-hospitalization Expense",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "post_hospitalization_expense"
            ),
            0.0,
        ),
        step=1000.0,
        key=f"post_expense_{selected_name}",
    )

with col4:
    pre_hospitalization_days_before = st.number_input(
        "Pre-hospitalization Days",
        min_value=0.0,
        value=numeric(
            defaults.get(
                "pre_hospitalization_days_before"
            ),
            0.0,
        ),
        step=1.0,
        key=f"pre_days_{selected_name}",
    )


post_hospitalization_days_after_discharge = st.number_input(
    "Post-hospitalization Days",
    min_value=0.0,
    value=numeric(
        defaults.get(
            "post_hospitalization_days_after_discharge"
        ),
        0.0,
    ),
    step=1.0,
    key=f"post_days_{selected_name}",
)


# ============================================================
# EVIDENCE
# ============================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    evidence_context_present = st.checkbox(
        "Sufficient evidence context is available",
        value=bool(
            defaults.get(
                "evidence_context_present",
                False,
            )
        ),
        key=f"evidence_context_{selected_name}",
    )

with col2:
    expense_timing_present = st.checkbox(
        "Expense timing evidence is available",
        value=bool(
            defaults.get(
                "expense_timing_present",
                False,
            )
        ),
        key=f"expense_timing_{selected_name}",
    )

with col3:
    same_condition_confirmed = tri_state(
        "Pre/Post expenses relate to same condition",
        defaults.get(
            "same_condition_confirmed"
        ),
        key=f"same_condition_{selected_name}",
    )


additional_information = st.text_area(
    "Additional Information",
    value=str(
        defaults.get(
            "additional_information",
            "",
        )
        or ""
    ),
    height=100,
    key=f"additional_info_{selected_name}",
)


# ============================================================
# BUILD PAYLOAD
# ============================================================

payload = {
    "case_id": case_id.strip(),

    "policy_start_date":
        policy_start_date.isoformat(),

    "claim_date":
        claim_date.isoformat(),

    "hospitalization_start_date":
        hospitalization_start_date.isoformat(),

    "hospitalization_end_date":
        hospitalization_end_date.isoformat(),

    "diagnosis":
        diagnosis.strip() or None,

    "treatment":
        treatment.strip() or None,

    "domiciliary_treatment":
        domiciliary_treatment,

    "experimental":
        experimental,

    "hospital_name":
        hospital_name.strip() or None,

    "hospital_registration":
        hospital_registration.strip() or None,

    "hospital_registered":
        hospital_registered,

    "hospital_minimum_criteria_documented":
        hospital_minimum_criteria_documented,

    "is_inpatient":
        is_inpatient,

    "treatment_duration_hours":
        treatment_duration_hours
        if treatment_duration_hours > 0
        else None,

    "hospital_room_unavailable":
        hospital_room_unavailable,

    "patient_cannot_be_moved":
        patient_cannot_be_moved,

    "medical_necessity_confirmed":
        medical_necessity_confirmed,

    "pre_existing_disease":
        pre_existing_disease,

    "prior_insurer":
        None,

    "prior_policy_insurer_type":
        None,

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
        basic_sum_insured
        if basic_sum_insured > 0
        else None,

    "claimed_amount":
        claimed_amount
        if claimed_amount > 0
        else None,

    "room_expense":
        room_expense
        if room_expense > 0
        else None,

    "icu_expense":
        icu_expense
        if icu_expense > 0
        else None,

    "doctor_expense":
        doctor_expense
        if doctor_expense > 0
        else None,

    "medicine_diagnostic_expense":
        medicine_diagnostic_expense
        if medicine_diagnostic_expense > 0
        else None,

    "pre_hospitalization_expense":
        pre_hospitalization_expense
        if pre_hospitalization_expense > 0
        else None,

    "post_hospitalization_expense":
        post_hospitalization_expense
        if post_hospitalization_expense > 0
        else None,

    "ambulance_expense":
        ambulance_expense
        if ambulance_expense > 0
        else None,

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

    "documents":
        [],

    "evidence_context_present":
        evidence_context_present,

    "expense_timing_present":
        expense_timing_present,

    "prior_policy_present":
        prior_policy_present,

    "dataset_continuous_coverage_months":
        continuous_coverage_months
        if continuous_coverage_months > 0
        else None,

    "additional_information":
        additional_information.strip() or None,
}


# ============================================================
# CRITICAL DEMO OVERRIDE
# ============================================================
#
# For evaluation/demo cases, the case definition is the
# source of truth.
#
# This prevents Streamlit widget state from carrying CUS-004's
# "Not provided" values into CUS-005, or vice versa.
#
# CUS-004:
#   hospital_registered = None
#   hospital_minimum_criteria_documented = None
#   medical_necessity_confirmed = None
#
# CUS-005:
#   hospital_registered = True
#   hospital_minimum_criteria_documented = True
#   medical_necessity_confirmed = True
#
# ============================================================

if selected_demo is not None:

    payload["hospital_registered"] = selected_demo.get(
        "hospital_registered"
    )

    payload["hospital_minimum_criteria_documented"] = (
        selected_demo.get(
            "hospital_minimum_criteria_documented"
        )
    )

    payload["medical_necessity_confirmed"] = (
        selected_demo.get(
            "medical_necessity_confirmed"
        )
    )

    payload["same_condition_confirmed"] = (
        selected_demo.get(
            "same_condition_confirmed"
        )
    )

    payload["prior_policy_records_received"] = (
        selected_demo.get(
            "prior_policy_records_received"
        )
    )

    payload["experimental"] = selected_demo.get(
        "experimental",
        False,
    )

    payload["evidence_context_present"] = (
        selected_demo.get(
            "evidence_context_present",
            False,
        )
    )

    payload["expense_timing_present"] = (
        selected_demo.get(
            "expense_timing_present",
            False,
        )
    )


# ============================================================
# REQUEST PAYLOAD
# ============================================================

with st.expander(
    "🔧 Request Payload",
    expanded=False,
):

    st.json(payload)


# ============================================================
# ANALYZE BUTTON
# ============================================================

st.divider()

analyze_button = st.button(
    "🔍 Analyze Claim",
    type="primary",
    use_container_width=True,
)


if analyze_button:

    if not api_available():

        st.error(
            "FastAPI backend is not running.\n\n"
            "Start it with:\n\n"
            "`uvicorn app.api.main:app --reload`"
        )

        st.stop()


    with st.spinner(
        "Running Case Analysis → Policy Retrieval → "
        "Coverage Analysis → Decision → Validation..."
    ):

        try:

            result = analyze_claim(
                payload
            )

        except requests.Timeout:

            st.error(
                "The backend request timed out."
            )

            st.stop()

        except Exception as exc:

            st.error(
                f"Claim analysis failed: {exc}"
            )

            st.stop()


    # ========================================================
    # RESULT DATA
    # ========================================================

    decision = result.get(
        "decision",
        "NEEDS_REVIEW",
    )

    confidence = result.get(
        "confidence",
        0.0,
    )

    payable_amount = result.get(
        "payable_amount"
    )

    deductions = result.get(
        "deductions",
        [],
    ) or []

    key_findings = result.get(
        "key_findings",
        [],
    ) or []

    applicable_limits = result.get(
        "applicable_limits",
        [],
    ) or []

    missing_evidence = result.get(
        "missing_evidence",
        [],
    ) or []

    citations = unique_citations(
        result.get(
            "citations",
            [],
        )
        or []
    )

    validation = result.get(
        "validation",
        {},
    ) or {}

    trace = result.get(
        "trace",
        [],
    ) or []


    # ========================================================
    # DECISION
    # ========================================================

    icon, message = decision_info(
        decision
    )

    if decision == "ADMISSIBLE":

        st.success(
            f"{icon} **{decision}**\n\n"
            f"{message}"
        )

    elif decision in {
        "ADMISSIBLE_WITH_LIMITS",
        "PARTIALLY_ADMISSIBLE",
    }:

        st.warning(
            f"{icon} **{decision}**\n\n"
            f"{message}"
        )

    elif decision == "NOT_ADMISSIBLE":

        st.error(
            f"{icon} **{decision}**\n\n"
            f"{message}"
        )

    elif decision == "NEEDS_REVIEW":

        st.info(
            f"{icon} **{decision}**\n\n"
            f"{message}"
        )

    else:

        st.info(
            f"{icon} **{decision}**\n\n"
            f"{message}"
        )


    # ========================================================
    # METRICS
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Decision",
            decision,
        )

    with col2:
        st.metric(
            "Confidence",
            f"{float(confidence) * 100:.0f}%",
        )

    with col3:
        st.metric(
            "Payable Amount",
            money(payable_amount),
        )

    with col4:

        total_deductions = sum(
            numeric(
                item.get(
                    "deduction"
                ),
                0,
            )
            for item in deductions
        )

        st.metric(
            "Total Deductions",
            money(total_deductions),
        )


    # ========================================================
    # FINDINGS
    # ========================================================

    st.header("🔎 Key Findings")

    if key_findings:

        for finding in key_findings:
            st.markdown(
                f"• {finding}"
            )

    else:

        st.caption(
            "No key findings returned."
        )


    # ========================================================
    # LIMITS
    # ========================================================

    st.header(
        "📏 Applicable Policy Limits"
    )

    if applicable_limits:

        for limit in applicable_limits:
            st.markdown(
                f"• {limit}"
            )

    else:

        st.caption(
            "No applicable limits returned."
        )


    # ========================================================
    # DEDUCTIONS
    # ========================================================

    st.header("💰 Deductions")

    if deductions:

        for item in deductions:

            category = item.get(
                "category",
                "unknown",
            )

            claimed = item.get(
                "claimed",
                0,
            )

            allowed = item.get(
                "allowed",
                0,
            )

            deduction = item.get(
                "deduction",
                0,
            )

            reason = item.get(
                "reason",
                "",
            )

            with st.container(
                border=True
            ):

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(
                        "**Category**"
                    )
                    st.write(
                        category.replace(
                            "_",
                            " ",
                        ).title()
                    )

                with col2:
                    st.markdown(
                        "**Claimed**"
                    )
                    st.write(
                        money(claimed)
                    )

                with col3:
                    st.markdown(
                        "**Allowed**"
                    )
                    st.write(
                        money(allowed)
                    )

                with col4:
                    st.markdown(
                        "**Deduction**"
                    )
                    st.write(
                        money(deduction)
                    )

                if reason:
                    st.caption(
                        reason
                    )

    else:

        st.caption(
            "No deductions."
        )


    # ========================================================
    # EVIDENCE
    # ========================================================

    st.header(
        "📂 Evidence Status"
    )

    if missing_evidence:

        st.warning(
            "Additional evidence is required before "
            "a final decision can be made."
        )

        for evidence in missing_evidence:

            st.markdown(
                f"• **{evidence}**"
            )

    else:

        st.success(
            "No missing evidence identified."
        )


    # ========================================================
    # VALIDATION
    # ========================================================

    validation_status = validation.get(
        "status",
        "UNKNOWN",
    )

    unsupported_claims = validation.get(
        "unsupported_claims",
        [],
    ) or []

    if validation_status == "VALID":

        st.success(
            f"Validation: **{validation_status}**"
        )

    elif validation_status == "VALID_ABSTENTION":

        st.info(
            f"Validation: **{validation_status}**"
        )

    else:

        st.error(
            f"Validation: **{validation_status}**"
        )

    if unsupported_claims:

        st.warning(
            "Unsupported claims detected:"
        )

        for claim in unsupported_claims:

            st.markdown(
                f"• {claim}"
            )


    # ========================================================
    # CITATIONS
    # ========================================================

    st.header(
        "📚 Policy Citations"
    )

    st.caption(
        f"{len(citations)} unique policy citations"
    )

    if citations:

        for index, citation in enumerate(
            citations,
            start=1,
        ):

            claim_text = citation.get(
                "claim",
                "",
            )

            with st.expander(
                f"Citation {index}: {claim_text}"
            ):

                st.write(
                    f"**Claim:** {claim_text}"
                )

                st.write(
                    f"**Source:** "
                    f"`{citation.get('source', '')}`"
                )

                st.write(
                    f"**Page:** "
                    f"`{citation.get('page', '')}`"
                )

                st.write(
                    f"**Section:** "
                    f"`{citation.get('section', '')}`"
                )

                st.write(
                    f"**Chunk ID:** "
                    f"`{citation.get('chunk_id', '')}`"
                )

    else:

        st.warning(
            "No policy citations were returned."
        )


    # ========================================================
    # AGENT TRACE
    # ========================================================

    st.header(
        "🤖 Agent Trace"
    )

    if trace:

        for index, step in enumerate(
            trace,
            start=1,
        ):

            agent = step.get(
                "agent",
                "UnknownAgent",
            )

            action = step.get(
                "action",
                "",
            )

            with st.expander(
                f"{index}. {agent}"
            ):

                st.write(
                    f"**Action:** {action}"
                )

                retrieval_count = step.get(
                    "retrieval_count"
                )

                if retrieval_count is not None:

                    st.write(
                        f"**Retrieval Count:** "
                        f"`{retrieval_count}`"
                    )

                validation_step = step.get(
                    "validation_status"
                )

                if validation_step is not None:

                    st.write(
                        f"**Validation Status:** "
                        f"`{validation_step}`"
                    )

                elapsed_ms = step.get(
                    "elapsed_ms"
                )

                if elapsed_ms is not None:

                    st.write(
                        f"**Elapsed:** "
                        f"`{float(elapsed_ms):.2f} ms`"
                    )

    else:

        st.caption(
            "No agent trace returned."
        )


    # ========================================================
    # RAW JSON
    # ========================================================

    st.header(
        "🧾 Raw Decision JSON"
    )

    with st.expander(
        "View machine-readable output"
    ):

        st.json(result)

    st.download_button(
        label="⬇️ Download Decision JSON",
        data=json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        ),
        file_name=(
            f"{case_id or 'claim'}_decision.json"
        ),
        mime="application/json",
        use_container_width=True,
    )
