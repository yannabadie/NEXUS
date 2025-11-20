"""
NEXUS V5.0 - Log Analyzer
Analyse exhaustive des logs JSONL pour générer des insights détaillés.
"""
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict, Counter
from datetime import datetime


class LogAnalyzer:
    """Analyseur de logs NEXUS."""

    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.events = []
        self.cfl_events = []
        self.session_id = None

    def load_logs(self):
        """Charge tous les logs JSONL."""
        # Find events file
        events_files = list(self.log_dir.glob("events_*.jsonl"))
        if events_files:
            events_file = events_files[0]
            self.session_id = events_file.stem.replace("events_", "")

            print(f"Loading events from {events_file}")
            with open(events_file, "r", encoding="utf-8") as f:
                for line in f:
                    self.events.append(json.loads(line))

        # Find CFL file
        cfl_files = list(self.log_dir.glob("cfl_*.jsonl"))
        if cfl_files:
            cfl_file = cfl_files[0]
            print(f"Loading CFL events from {cfl_file}")
            with open(cfl_file, "r", encoding="utf-8") as f:
                for line in f:
                    self.cfl_events.append(json.loads(line))

        print(f"Loaded {len(self.events)} events and {len(self.cfl_events)} CFL events")

    def analyze_overview(self) -> Dict[str, Any]:
        """Analyse générale de la session."""
        if not self.events:
            return {}

        first_event = self.events[0]
        last_event = self.events[-1]

        start_time = datetime.fromisoformat(first_event["timestamp"])
        end_time = datetime.fromisoformat(last_event["timestamp"])
        duration = (end_time - start_time).total_seconds()

        event_types = Counter(e["event_type"] for e in self.events)

        return {
            "session_id": self.session_id,
            "start_time": first_event["timestamp"],
            "end_time": last_event["timestamp"],
            "duration_seconds": duration,
            "total_events": len(self.events),
            "event_types": dict(event_types)
        }

    def analyze_turns(self) -> Dict[str, Any]:
        """Analyse des tours."""
        turn_starts = [e for e in self.events if e["event_type"] == "TURN_START"]
        turn_ends = [e for e in self.events if e["event_type"] == "TURN_END"]

        turns = []
        for start in turn_starts:
            turn_num = start["data"]["iteration"]
            turn_events = [e for e in self.events if e["data"].get("turn") == turn_num]

            turn_info = {
                "turn": turn_num,
                "active_agent": start["data"]["active_agent"],
                "total_events": len(turn_events),
                "event_types": Counter(e["event_type"] for e in turn_events)
            }

            # Find agent invocation
            invocations = [e for e in turn_events if e["event_type"] == "AGENT_INVOCATION"]
            if invocations:
                turn_info["agent_invoked"] = invocations[0]["data"]["agent"]

            # Find agent response
            responses = [e for e in turn_events if e["event_type"] == "AGENT_RESPONSE"]
            if responses:
                resp = responses[0]
                turn_info["response_duration"] = resp["data"]["duration_seconds"]
                turn_info["action_type"] = resp["data"]["action_type"]

            # Find tool executions
            tool_execs = [e for e in turn_events if e["event_type"] == "TOOL_EXECUTION"]
            if tool_execs:
                turn_info["tools_used"] = [t["data"]["tool_name"] for t in tool_execs]
                turn_info["tool_statuses"] = [t["data"]["status"] for t in tool_execs]

            turns.append(turn_info)

        return {
            "total_turns": len(turn_starts),
            "turns": turns
        }

    def analyze_cfl(self) -> Dict[str, Any]:
        """Analyse du Cognitive Feedback Loop."""
        if not self.cfl_events:
            return {}

        tool_executions = [e for e in self.cfl_events if e["phase"] == "TOOL_EXECUTION_START"]
        reviews = [e for e in self.cfl_events if e["phase"] == "POST_ACTION_REVIEW"]

        cfl_cycles = []
        for tool_exec in tool_executions:
            turn = tool_exec["turn"]
            tool_name = tool_exec["data"]["tool_name"]

            # Find corresponding review
            review = next((r for r in reviews if r["turn"] == turn + 1), None)

            cycle = {
                "turn": turn,
                "tool": tool_name,
                "expected_outcome": tool_exec["data"]["expected_outcome"],
                "reviewed": review is not None
            }

            if review:
                cycle["validation_status"] = review["data"]["validation_status"]
                cycle["has_discrepancies"] = review["data"]["has_discrepancies"]

            cfl_cycles.append(cycle)

        # CFL compliance
        total_tools = len(tool_executions)
        reviewed = sum(1 for c in cfl_cycles if c["reviewed"])
        compliance_rate = (reviewed / total_tools * 100) if total_tools > 0 else 0

        validation_statuses = Counter(
            c["validation_status"] for c in cfl_cycles if "validation_status" in c
        )

        return {
            "total_tool_executions": total_tools,
            "reviewed": reviewed,
            "compliance_rate": compliance_rate,
            "validation_statuses": dict(validation_statuses),
            "cycles": cfl_cycles
        }

    def analyze_tools(self) -> Dict[str, Any]:
        """Analyse de l'utilisation des outils."""
        tool_events = [e for e in self.events if e["event_type"] == "TOOL_EXECUTION"]

        if not tool_events:
            return {}

        tools_used = Counter(e["data"]["tool_name"] for e in tool_events)
        tool_statuses = defaultdict(lambda: {"SUCCESS": 0, "FAILURE": 0, "ERROR": 0})

        for event in tool_events:
            tool = event["data"]["tool_name"]
            status = event["data"]["status"]
            tool_statuses[tool][status] += 1

        return {
            "total_executions": len(tool_events),
            "tools_used": dict(tools_used),
            "success_rates": {
                tool: {
                    "total": sum(statuses.values()),
                    "success": statuses["SUCCESS"],
                    "failure": statuses["FAILURE"],
                    "error": statuses["ERROR"],
                    "success_rate": (
                        statuses["SUCCESS"] / sum(statuses.values()) * 100
                        if sum(statuses.values()) > 0 else 0
                    )
                }
                for tool, statuses in tool_statuses.items()
            }
        }

    def analyze_errors(self) -> Dict[str, Any]:
        """Analyse des erreurs."""
        error_events = [e for e in self.events if e["event_type"] == "ERROR"]

        if not error_events:
            return {"total_errors": 0, "errors": []}

        error_types = Counter(e["data"]["error_type"] for e in error_events)

        errors_by_turn = defaultdict(list)
        for event in error_events:
            turn = event["data"]["turn"]
            errors_by_turn[turn].append({
                "type": event["data"]["error_type"],
                "message": event["data"]["error_message"]
            })

        return {
            "total_errors": len(error_events),
            "error_types": dict(error_types),
            "errors_by_turn": dict(errors_by_turn),
            "errors": error_events
        }

    def analyze_performance(self) -> Dict[str, Any]:
        """Analyse de performance."""
        agent_responses = [e for e in self.events if e["event_type"] == "AGENT_RESPONSE"]

        if not agent_responses:
            return {}

        durations = [e["data"]["duration_seconds"] for e in agent_responses]
        avg_duration = sum(durations) / len(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        # Performance by agent
        by_agent = defaultdict(list)
        for event in agent_responses:
            agent = event["data"]["agent"]
            duration = event["data"]["duration_seconds"]
            by_agent[agent].append(duration)

        agent_performance = {}
        for agent, durs in by_agent.items():
            agent_performance[agent] = {
                "calls": len(durs),
                "avg_duration": sum(durs) / len(durs),
                "min_duration": min(durs),
                "max_duration": max(durs)
            }

        return {
            "total_agent_calls": len(agent_responses),
            "avg_response_time": avg_duration,
            "min_response_time": min_duration,
            "max_response_time": max_duration,
            "by_agent": agent_performance
        }

    def analyze_validation(self) -> Dict[str, Any]:
        """Analyse des validations."""
        validation_events = [e for e in self.events if e["event_type"] == "VALIDATION"]

        if not validation_events:
            return {}

        validation_types = Counter(e["data"]["validation_type"] for e in validation_events)
        validation_results = Counter(e["data"]["result"] for e in validation_events)

        failures = [e for e in validation_events if e["data"]["result"] == "FAILURE"]

        return {
            "total_validations": len(validation_events),
            "validation_types": dict(validation_types),
            "results": dict(validation_results),
            "failures": len(failures),
            "failure_details": [
                {
                    "turn": e["data"]["turn"],
                    "type": e["data"]["validation_type"],
                    "details": e["data"].get("details", {})
                }
                for e in failures
            ]
        }

    def generate_report(self, output_path: Path):
        """Génère un rapport complet d'analyse."""
        print("Analyzing logs...")

        overview = self.analyze_overview()
        turns = self.analyze_turns()
        cfl = self.analyze_cfl()
        tools = self.analyze_tools()
        errors = self.analyze_errors()
        performance = self.analyze_performance()
        validation = self.analyze_validation()

        report = {
            "session_id": self.session_id,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "overview": overview,
            "turns": turns,
            "cfl": cfl,
            "tools": tools,
            "errors": errors,
            "performance": performance,
            "validation": validation
        }

        # Save JSON report
        json_path = output_path / f"analysis_{self.session_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"JSON report saved to: {json_path}")

        # Generate Markdown report
        md_path = output_path / f"analysis_{self.session_id}.md"
        self._generate_markdown_report(report, md_path)

        print(f"Markdown report saved to: {md_path}")

    def _generate_markdown_report(self, report: Dict, path: Path):
        """Génère un rapport Markdown lisible."""
        lines = [
            f"# NEXUS V5.0 - LOG ANALYSIS REPORT",
            "",
            f"**Session ID:** {report['session_id']}",
            f"**Analysis Date:** {report['analysis_timestamp']}",
            "",
            "## 📊 Overview",
            ""
        ]

        if report["overview"]:
            o = report["overview"]
            lines.extend([
                f"- **Duration:** {o['duration_seconds']:.2f} seconds",
                f"- **Total Events:** {o['total_events']}",
                f"- **Start Time:** {o['start_time']}",
                f"- **End Time:** {o['end_time']}",
                ""
            ])

        # Turns
        if report["turns"]:
            t = report["turns"]
            lines.extend([
                "## 🔄 Turns Analysis",
                "",
                f"**Total Turns:** {t['total_turns']}",
                ""
            ])

            for turn in t["turns"][:10]:  # First 10 turns
                lines.append(f"### Turn {turn['turn']}")
                lines.append(f"- Agent: {turn['active_agent']}")
                if "action_type" in turn:
                    lines.append(f"- Action: {turn['action_type']}")
                if "tools_used" in turn:
                    lines.append(f"- Tools: {', '.join(turn['tools_used'])}")
                if "response_duration" in turn:
                    lines.append(f"- Duration: {turn['response_duration']:.2f}s")
                lines.append("")

        # CFL
        if report["cfl"]:
            c = report["cfl"]
            lines.extend([
                "## 🔁 CFL Analysis",
                "",
                f"**Total Tool Executions:** {c['total_tool_executions']}",
                f"**Reviewed:** {c['reviewed']}",
                f"**Compliance Rate:** {c['compliance_rate']:.1f}%",
                ""
            ])

            if c.get("validation_statuses"):
                lines.append("**Validation Statuses:**")
                for status, count in c["validation_statuses"].items():
                    lines.append(f"- {status}: {count}")
                lines.append("")

        # Tools
        if report["tools"]:
            t = report["tools"]
            lines.extend([
                "## 🛠️ Tools Analysis",
                "",
                f"**Total Executions:** {t['total_executions']}",
                "",
                "**Tools Used:**"
            ])

            for tool, count in t["tools_used"].items():
                success_rate = t["success_rates"][tool]["success_rate"]
                lines.append(f"- {tool}: {count} executions ({success_rate:.1f}% success)")

            lines.append("")

        # Errors
        if report["errors"]:
            e = report["errors"]
            lines.extend([
                "## ❌ Errors Analysis",
                "",
                f"**Total Errors:** {e['total_errors']}",
                ""
            ])

            if e.get("error_types"):
                lines.append("**Error Types:**")
                for error_type, count in e["error_types"].items():
                    lines.append(f"- {error_type}: {count}")
                lines.append("")

        # Performance
        if report["performance"]:
            p = report["performance"]
            lines.extend([
                "## ⚡ Performance Analysis",
                "",
                f"**Total Agent Calls:** {p['total_agent_calls']}",
                f"**Avg Response Time:** {p['avg_response_time']:.2f}s",
                f"**Min Response Time:** {p['min_response_time']:.2f}s",
                f"**Max Response Time:** {p['max_response_time']:.2f}s",
                ""
            ])

            if p.get("by_agent"):
                lines.append("**By Agent:**")
                for agent, stats in p["by_agent"].items():
                    lines.append(f"- {agent}: {stats['calls']} calls, avg {stats['avg_duration']:.2f}s")
                lines.append("")

        # Validation
        if report["validation"]:
            v = report["validation"]
            lines.extend([
                "## ✓ Validation Analysis",
                "",
                f"**Total Validations:** {v['total_validations']}",
                f"**Failures:** {v['failures']}",
                ""
            ])

            if v.get("results"):
                lines.append("**Results:**")
                for result, count in v["results"].items():
                    lines.append(f"- {result}: {count}")
                lines.append("")

        # Write report
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="NEXUS V5.0 Log Analyzer")
    parser.add_argument("log_dir", type=Path, help="Directory containing log files")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory for reports (default: same as log_dir)"
    )

    args = parser.parse_args()

    if not args.log_dir.exists():
        print(f"Error: Log directory not found: {args.log_dir}")
        return

    output_dir = args.output or args.log_dir

    analyzer = LogAnalyzer(args.log_dir)
    analyzer.load_logs()
    analyzer.generate_report(output_dir)

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
