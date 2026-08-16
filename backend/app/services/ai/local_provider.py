class LocalAnalysisProvider:
    """Safe local explanation layer used until an external AI provider is configured."""

    def explain(self, metrics: dict) -> dict:
        recommendations = []
        for position in metrics["positions"]:
            if position["allocation_percent"] > metrics["policy"]["max_single_holding"]:
                recommendations.append({
                    "action": "review",
                    "symbol": position["symbol"],
                    "reason": "Review this position because it is above the selected single-holding policy limit.",
                    "risks": ["Reducing a position can have tax and timing consequences."],
                    "confidence": "high",
                })
        if metrics["missing_symbols"]:
            recommendations.append({
                "action": "research",
                "symbol": metrics["missing_symbols"][0],
                "reason": "Review the symbol because current market data was unavailable.",
                "risks": ["Portfolio totals may be incomplete while market data is missing."],
                "confidence": "low",
            })
        return {
            "summary": "The portfolio was evaluated using deterministic allocation and cash policies.",
            "recommendations": recommendations,
            "disclaimer": "This is informational research, not investment, tax, or legal advice.",
        }
