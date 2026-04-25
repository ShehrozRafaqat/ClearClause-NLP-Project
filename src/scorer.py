"""
Module 3 – Risk Scorer
Calculates the numerical risk score based on detected clauses.
"""
from __future__ import annotations
import plotly.graph_objects as go
from src.extractor import DetectedClause


def calculate_risk(clauses: list[DetectedClause], expected_total: int = 100) -> tuple[int, str]:
    """
    Calculate the total risk score (0-100) and return the category.
    Formula: min(100, (sum of clause risk scores / expected) * 100)
    """
    total = sum(c.risk_score for c in clauses)
    
    # Cap at 100
    score = min(100, int((total / expected_total) * 100))
    if not clauses:
        return 0, "Safe"

    if score < 34:
        return score, "Safe"
    elif score < 67:
        return score, "Review Carefully"
    else:
        return score, "High Risk"


def plot_risk_gauge(score: int, category: str) -> go.Figure:
    """Create a Plotly gauge chart for the risk score."""
    if score < 34:
        color = "#16A34A"  # Green
    elif score < 67:
        color = "#D97706"  # Amber
    else:
        color = "#DC2626"  # Red

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': f"<br><span style='font-size:1.5vw; color:{color}'>{category}</span>", 'font': {'size': 24, "color": "#0A1628"}},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#CBD5E1",
            'steps': [
                {'range': [0, 33], 'color': '#DCFCE7'},
                {'range': [33, 66], 'color': '#FEF3C7'},
                {'range': [66, 100], 'color': '#FEE2E2'}
            ],
        }
    ))
    
    fig.update_layout(
        font={'family': "Inter, sans-serif"},
        margin=dict(l=20, r=20, t=50, b=20),
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
