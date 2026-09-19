from typing import Any

from app.orchestrator.state import ClaimEngineState
from app.schemas.decision import (
    Citation,
    DecisionOutput,
    ValidationResult,
    TraceStep,
)


class DecisionAgent:
    """
    Converts structured coverage analysis into a machine-readable
    claim decision.

    Decision precedence:

    1. Clear exclusion / failed waiting period -> NOT_ADMISSIBLE
    2. Material missing evidence -> NEEDS_REVIEW
    3. Eligible claim with deductions -> ADMISSIBLE_WITH_LIMITS
    4. Eligible claim without deductions -> ADMISSIBLE
    5. Pre/post component rejection -> PARTIALLY_ADMISSIBLE
    """

    def run(self, state: ClaimEngineState) -> ClaimEngineState:
        claim = state["claim"]
        coverage = state.get("coverage_analysis", {})
        policy_evidence = state.get("policy_evidence", [])

        trace = state.setdefault("trace", [])

        # ---------------------------------------------------------
        # 1. Extract structured coverage results
        # ---------------------------------------------------------

        exclusions = coverage.get(
            "exclusions",
            [],
        )

        # CoverageAgent currently uses "waiting_failures".
        # The fallback keeps compatibility with the older key.
        waiting_failures = coverage.get(
            "waiting_failures",
            coverage.get(
                "waiting_period_failures",
                [],
            ),
        )

        missing_evidence = coverage.get(
            "missing_evidence",
            [],
        )

        findings = coverage.get(
            "findings",
            [],
        )

        applicable_limits = coverage.get(
            "applicable_limits",
            [],
        )

        deductions = coverage.get(
            "deductions",
            [],
        )

        # ---------------------------------------------------------
        # 2. Determine decision
        # ---------------------------------------------------------

        decision = "ADMISSIBLE"
        confidence = 0.80

        # Material missing evidence requires abstention.
        # We must not convert an unresolved eligibility fact
        # into a definitive rejection.
        if missing_evidence:
            decision = "NEEDS_REVIEW"
            confidence = 0.40

        # Clear exclusions and failed waiting periods are
        # definitive only when the required evidence is present.
        elif exclusions or waiting_failures:
            decision = "NOT_ADMISSIBLE"
            confidence = 0.90

        # Valid claim with applicable deductions.
        elif deductions:
            decision = "ADMISSIBLE_WITH_LIMITS"
            confidence = 0.85

        else:
            decision = "ADMISSIBLE"
            confidence = 0.80

        # ---------------------------------------------------------
        # 3. Detect partial admissibility
        # ---------------------------------------------------------

        partial_categories = {
            "pre_hospitalization",
            "post_hospitalization",
        }

        deducted_categories = {
            item.get("category")
            for item in deductions
            if isinstance(item, dict)
        }

        # PARTIALLY_ADMISSIBLE is used only when the deductions
        # represent rejected pre/post components rather than
        # ordinary policy sub-limit deductions.
        if (
            not exclusions
            and not waiting_failures
            and not missing_evidence
            and deducted_categories
            and deducted_categories.issubset(
                partial_categories
            )
        ):
            decision = "PARTIALLY_ADMISSIBLE"
            confidence = 0.80

        # ---------------------------------------------------------
        # 4. Build key findings
        # ---------------------------------------------------------

        key_findings = list(findings)

        if waiting_failures:
            key_findings.extend(
                waiting_failures
            )

        if exclusions:
            key_findings.extend(
                exclusions
            )

        key_findings = self._deduplicate(
            key_findings
        )

        # ---------------------------------------------------------
        # 5. Build citations
        # ---------------------------------------------------------

        citations = self._build_citations(
            policy_evidence=policy_evidence,
            findings=key_findings,
            applicable_limits=applicable_limits,
            exclusions=exclusions,
            waiting_failures=waiting_failures,
        )

        # ---------------------------------------------------------
        # 6. Calculate payable amount
        # ---------------------------------------------------------

        # CoverageAgent provides provisional_payable.
        payable_amount = coverage.get(
            "provisional_payable"
        )

        # Backward-compatible fallback.
        if payable_amount is None:
            payable_amount = coverage.get(
                "payable_amount"
            )

        # Last-resort calculation.
        if (
            payable_amount is None
            and claim.claimed_amount is not None
        ):
            total_deductions = sum(
                float(
                    item.get(
                        "deduction",
                        item.get(
                            "amount",
                            0,
                        ),
                    )
                    or 0
                )
                for item in deductions
                if isinstance(item, dict)
            )

            payable_amount = max(
                0.0,
                float(claim.claimed_amount)
                - total_deductions,
            )

        # A rejected claim has zero payable amount.
        if decision == "NOT_ADMISSIBLE":
            payable_amount = 0.0

        # An abstention has no definitive payable amount.
        if decision == "NEEDS_REVIEW":
            payable_amount = None

        # ---------------------------------------------------------
        # 7. Validation starts as pending
        # ---------------------------------------------------------

        validation = ValidationResult(
            status="PENDING",
            unsupported_claims=[],
        )

        # ---------------------------------------------------------
        # 8. Create machine-readable decision
        # ---------------------------------------------------------

        output = DecisionOutput(
            case_id=claim.case_id,
            decision=decision,
            confidence=confidence,
            key_findings=key_findings,
            applicable_limits=self._deduplicate(
                applicable_limits
            ),
            missing_evidence=self._deduplicate(
                missing_evidence
            ),
            citations=citations,
            validation=validation,
            trace=[],
            payable_amount=payable_amount,
            deductions=deductions,
        )

        state["decision"] = output

        # ---------------------------------------------------------
        # 9. Trace
        # ---------------------------------------------------------

        trace.append(
            {
                "agent": "DecisionAgent",
                "action": (
                    f"Generated {decision} from structured "
                    "coverage analysis, policy exclusions, "
                    "waiting periods, missing evidence, "
                    "and deductions."
                ),
                "retrieval_count": len(
                    policy_evidence
                ),
            }
        )

        # Include the accumulated trace in the final output.
        output.trace = [
            TraceStep(**item)
            for item in trace
        ]

        return state

    # =============================================================
    # Citation construction
    # =============================================================

    def _build_citations(
        self,
        policy_evidence: list[dict[str, Any]],
        findings: list[str],
        applicable_limits: list[str],
        exclusions: list[str],
        waiting_failures: list[str],
    ) -> list[Citation]:

        citations: list[Citation] = []

        if not policy_evidence:
            return citations

        relevant_text = " ".join(
            findings
            + applicable_limits
            + exclusions
            + waiting_failures
        ).lower()

        selected: list[
            tuple[int, dict[str, Any]]
        ] = []

        # Score retrieved evidence according to overlap with
        # the actual structured decision information.
        for evidence in policy_evidence:

            text = str(
                evidence.get("text")
                or evidence.get("content")
                or ""
            ).lower()

            score = self._citation_relevance(
                relevant_text,
                text,
            )

            selected.append(
                (
                    score,
                    evidence,
                )
            )

        selected.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        # Limit final citations.
        for _, evidence in selected[:8]:

            chunk_id = evidence.get(
                "chunk_id"
            )

            page = evidence.get(
                "page"
            )

            section = evidence.get(
                "section"
            )

            source = evidence.get(
                "source"
            )

            # Never fabricate citation metadata.
            if (
                chunk_id is None
                or page is None
                or section is None
                or source is None
            ):
                continue

            claim_text = self._citation_claim(
                evidence=evidence,
                findings=findings,
                applicable_limits=applicable_limits,
                exclusions=exclusions,
                waiting_failures=waiting_failures,
            )

            citations.append(
                Citation(
                    claim=claim_text,
                    source=str(source),
                    page=int(page),
                    section=str(section),
                    chunk_id=str(chunk_id),
                )
            )

        return citations

    # =============================================================
    # Citation relevance
    # =============================================================

    @staticmethod
    def _citation_relevance(
        query_text: str,
        evidence_text: str,
    ) -> int:

        if not evidence_text:
            return 0

        query_terms = {
            word.strip(
                ".,:;()[]{}"
            )
            for word in query_text.split()
            if len(
                word.strip(
                    ".,:;()[]{}"
                )
            ) >= 4
        }

        evidence_terms = {
            word.strip(
                ".,:;()[]{}"
            )
            for word in evidence_text.split()
            if len(
                word.strip(
                    ".,:;()[]{}"
                )
            ) >= 4
        }

        return len(
            query_terms.intersection(
                evidence_terms
            )
        )

    # =============================================================
    # Citation claim
    # =============================================================

    @staticmethod
    def _citation_claim(
        evidence: dict[str, Any],
        findings: list[str],
        applicable_limits: list[str],
        exclusions: list[str],
        waiting_failures: list[str],
    ) -> str:

        text = str(
            evidence.get("text")
            or evidence.get("content")
            or ""
        ).strip()

        lower_text = text.lower()

        # ---------------------------------------------------------
        # Findings
        # ---------------------------------------------------------

        for finding in findings:

            finding_lower = finding.lower()

            if (
                "waiting" in finding_lower
                and "waiting" in lower_text
            ):
                return finding

            if (
                "pre-existing" in finding_lower
                and (
                    "pre-existing" in lower_text
                    or "pre existing" in lower_text
                )
            ):
                return finding

            if (
                "day-care" in finding_lower
                and "day care" in lower_text
            ):
                return finding

            if (
                "domiciliary" in finding_lower
                and "domiciliary" in lower_text
            ):
                return finding

            if (
                "hospital" in finding_lower
                and "hospital" in lower_text
            ):
                return finding

        # ---------------------------------------------------------
        # Applicable limits
        # ---------------------------------------------------------

        for limit in applicable_limits:

            if any(
                keyword in lower_text
                for keyword in (
                    "1%",
                    "2%",
                    "25%",
                    "40%",
                    "20%",
                    "ambulance",
                    "room rent",
                    "icu",
                    "medical practitioner",
                    "diagnostic",
                )
            ):
                return limit

        # ---------------------------------------------------------
        # Exclusions
        # ---------------------------------------------------------

        for exclusion in exclusions:

            if any(
                keyword in lower_text
                for keyword in (
                    "cosmetic",
                    "aesthetic",
                    "experimental",
                    "unproven",
                    "exclusion",
                )
            ):
                return exclusion

        # ---------------------------------------------------------
        # Waiting failures
        # ---------------------------------------------------------

        for failure in waiting_failures:

            if "waiting" in lower_text:
                return failure

        # ---------------------------------------------------------
        # Fallback
        # ---------------------------------------------------------

        if len(text) > 180:
            text = (
                text[:177].rstrip()
                + "..."
            )

        return (
            text
            or "Policy provision supporting claim analysis."
        )

    # =============================================================
    # Utility
    # =============================================================

    @staticmethod
    def _deduplicate(
        values: list[Any],
    ) -> list[Any]:

        result: list[Any] = []
        seen: set[str] = set()

        for value in values:

            key = str(value).strip()

            if not key or key in seen:
                continue

            seen.add(key)
            result.append(value)

        return result