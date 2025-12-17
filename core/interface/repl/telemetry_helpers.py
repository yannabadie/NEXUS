"""
NEXUS V10.2 - Telemetry Command Helpers

Extracted helper functions for /telemetry commands.

Usage:
    from core.interface.repl.telemetry_helpers import (
        format_telemetry_report,
        export_telemetry_csv
    )
"""

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import csv

logger = logging.getLogger("nexus.repl.telemetry")


def format_telemetry_report(metrics: Dict, days: int = 7) -> str:
    """
    Format telemetry metrics as a report string.
    
    Args:
        metrics: Metrics dict from TelemetryExporter
        days: Number of days to report
        
    Returns:
        Formatted report string
    """
    lines = [
        f"## Telemetry Report (Last {days} days)",
        "",
        "| Metric | Value |",
        "|--------|-------|"
    ]
    
    lines.append(f"| Total Tasks | {metrics.get('total_tasks', 0)} |")
    lines.append(f"| Success Rate | {metrics.get('success_rate', 0):.1%} |")
    lines.append(f"| Avg Duration | {metrics.get('avg_duration', 0):.2f}s |")
    lines.append(f"| Total Tokens | {metrics.get('total_tokens', 0):,} |")
    lines.append(f"| Total Cost | ${metrics.get('total_cost', 0):.4f} |")
    
    return "\n".join(lines)


def format_agent_metrics(metrics: Dict) -> str:
    """
    Format per-agent metrics.
    
    Args:
        metrics: Agent metrics dict
        
    Returns:
        Formatted string
    """
    lines = [
        "",
        "### Agent Performance",
        "",
        "| Agent | Tasks | Avg Duration | Success |",
        "|-------|-------|--------------|---------|"
    ]
    
    agents = metrics.get("by_agent", {})
    for agent, data in agents.items():
        lines.append(
            f"| {agent} | {data.get('count', 0)} | "
            f"{data.get('avg_duration', 0):.2f}s | "
            f"{data.get('success_rate', 0):.0%} |"
        )
    
    return "\n".join(lines)


def export_telemetry_csv(
    metrics: Dict,
    output_path: Path,
    filename: str = None
) -> Path:
    """
    Export telemetry to CSV file.
    
    Args:
        metrics: Metrics dict
        output_path: Directory for output
        filename: Optional filename override
        
    Returns:
        Path to created CSV file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"telemetry_{timestamp}.csv"
    
    output_file = output_path / filename
    
    rows = metrics.get("rows", [])
    if not rows:
        # Create summary row
        rows = [{
            "timestamp": datetime.now().isoformat(),
            "total_tasks": metrics.get("total_tasks", 0),
            "success_rate": metrics.get("success_rate", 0),
            "total_tokens": metrics.get("total_tokens", 0),
            "total_cost": metrics.get("total_cost", 0)
        }]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    return output_file


def calculate_cost_trend(costs: List[Dict], days: int = 7) -> Dict:
    """
    Calculate cost trend over time.
    
    Args:
        costs: List of cost records with timestamp and amount
        days: Number of days to analyze
        
    Returns:
        Trend analysis dict
    """
    if not costs:
        return {"trend": "stable", "change": 0.0}
    
    cutoff = datetime.now() - timedelta(days=days)
    recent = [c for c in costs if datetime.fromisoformat(c.get("timestamp", "")) > cutoff]
    
    if len(recent) < 2:
        return {"trend": "insufficient_data", "change": 0.0}
    
    # Simple trend: compare first half to second half
    mid = len(recent) // 2
    first_half = sum(c.get("amount", 0) for c in recent[:mid])
    second_half = sum(c.get("amount", 0) for c in recent[mid:])
    
    if first_half == 0:
        return {"trend": "increasing" if second_half > 0 else "stable", "change": 0.0}
    
    change = (second_half - first_half) / first_half
    
    if change > 0.1:
        trend = "increasing"
    elif change < -0.1:
        trend = "decreasing"
    else:
        trend = "stable"
    
    return {"trend": trend, "change": change}
