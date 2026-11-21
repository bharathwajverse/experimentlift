"""Rendering functions intentionally consume only computed report fields."""

from __future__ import annotations

import json

from .models import AnalysisReport


def as_json(report: AnalysisReport) -> str:
    return report.model_dump_json(indent=2)


def as_markdown(report: AnalysisReport) -> str:
    critical_issue_text = ", ".join(report.critical_issues) or "None"
    warning_text = ", ".join(report.warnings) or "None"
    effect = "not estimable" if report.risk_difference is None else f"{report.risk_difference:.2%}"
    return "\n".join(
        [
            "# ExperimentLift synthetic analysis",
            "",
            "> **SYNTHETIC DATA ONLY - not a customer or campaign result.**",
            "",
            f"- Status: **{report.status}**",
            f"- Validity: **{report.validity}**",
            f"- Verdict: **{report.verdict}**",
            f"- Absolute conversion difference (treatment - control): **{effect}**",
            f"- Critical issues: {critical_issue_text}",
            f"- Warnings: {warning_text}",
        ]
    )
