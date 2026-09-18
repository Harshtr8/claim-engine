from langgraph.graph import END, START, StateGraph

from app.agents.case_analysis import CaseAnalysisAgent
from app.agents.policy_evidence import PolicyEvidenceAgent
from app.agents.coverage import CoverageAgent
from app.agents.decision import DecisionAgent
from app.agents.validation import ValidationAgent
from app.orchestrator.state import ClaimEngineState
from app.schemas.claim import ClaimCase


class ClaimEngine:

    def __init__(self):
        self.case_analysis_agent = CaseAnalysisAgent()
        self.policy_evidence_agent = PolicyEvidenceAgent()
        self.coverage_agent = CoverageAgent()
        self.decision_agent = DecisionAgent()
        self.validation_agent = ValidationAgent()

        self.graph = self._build_graph()

    def _case_analysis(self, state):
        return self.case_analysis_agent.run(state)

    def _policy_evidence(self, state):
        return self.policy_evidence_agent.run(state)

    def _coverage(self, state):
        return self.coverage_agent.run(state)

    def _decision(self, state):
        return self.decision_agent.run(state)

    def _validation(self, state):
        return self.validation_agent.run(state)

    def _build_graph(self):

        builder = StateGraph(ClaimEngineState)

        builder.add_node(
            "case_analysis",
            self._case_analysis,
        )

        builder.add_node(
            "policy_evidence",
            self._policy_evidence,
        )

        builder.add_node(
            "coverage",
            self._coverage,
        )

        builder.add_node(
            "decision",
            self._decision,
        )

        builder.add_node(
            "validation",
            self._validation,
        )

        builder.add_edge(
            START,
            "case_analysis",
        )

        builder.add_edge(
            "case_analysis",
            "policy_evidence",
        )

        builder.add_edge(
            "policy_evidence",
            "coverage",
        )

        builder.add_edge(
            "coverage",
            "decision",
        )

        builder.add_edge(
            "decision",
            "validation",
        )

        builder.add_edge(
            "validation",
            END,
        )

        return builder.compile()

    def analyze(self, claim: ClaimCase):

        initial_state: ClaimEngineState = {
            "claim": claim,
            "trace": [],
        }

        return self.graph.invoke(
            initial_state
        )