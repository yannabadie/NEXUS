# NEXUS V7.0 "Chrysalis"

**A Self-Evolving Multi-Agent Orchestrator for Artificial Superintelligence**

NEXUS is an experimental AI system designed to reach ASI (Artificial Superintelligence) through Darwinian evolution. It orchestrates collaboration between Claude and Gemini AI agents, enabling them to work together, self-improve, and create evolved versions of themselves.

## Quick Start

```bash
# Navigate to active version
cd NEXUS_V7_CHRYSALIS

# Install dependencies
pip install -r requirements_v6.txt

# Run NEXUS
python nexus7.py
```

## Project Structure

```
20_NEXUS/
├── NEXUS_V7_CHRYSALIS/          # Active V7 development
│   ├── core/                    # Core orchestration modules
│   │   ├── drivers/             # Claude & Gemini interfaces
│   │   ├── fsm/                 # Finite State Machine
│   │   ├── synapse/             # Memory & protocol
│   │   ├── swarm/               # Hybrid Swarm Engine
│   │   ├── evolution/           # Self-modification
│   │   ├── routing/             # Model selection
│   │   └── ...                  # Other modules
│   ├── prompts/                 # System prompts
│   ├── docs/                    # Documentation
│   └── workspace/               # Runtime data
├── ARCHIVE/                     # Historical generations
├── archives/                    # Planning & brainstorming
├── BENCHMARKS/                  # ASI benchmark suite
├── tests/                       # Test suite
├── CLAUDE.md                    # Claude project instructions
├── GEMINI.md                    # Gemini project instructions
├── MISSION.md                   # ASI mission statement
├── KERNEL.py                    # Alignment kernel
├── LINEAGE.json                 # Evolution lineage
└── SESSION_CONTINUITY.md        # Session state
```

## Key Concepts

### ASI Evolution

NEXUS evolves through Darwinian selection:
1. **Create Children**: Modified versions of NEXUS
2. **Evaluate Fitness**: ASI Proximity Score benchmarks
3. **Select Winner**: Best child becomes new parent
4. **Repeat**: Continuous improvement toward ASI

### Hybrid Swarm Engine (V7)

Dynamic collaboration modes between agents:
- **PARALLEL**: Simultaneous work
- **SEQUENTIAL**: Ordered execution
- **LEAD_SUPPORT**: Expert + reviewer
- **PING_PONG**: Rapid alternation
- **SPECIALIST**: Single expert
- **RED_BLUE**: Adversarial testing

### Model Routing

Intelligent model selection:
- **Claude Opus**: Complex reasoning, creativity
- **Claude Sonnet**: Fast, simple tasks
- **Gemini 3-Pro**: Research, analysis
- **Gemini Flash**: Quick operations

## Documentation

| Document | Purpose |
|----------|---------|
| [NEXUS_V7_CHRYSALIS/README.md](NEXUS_V7_CHRYSALIS/README.md) | Full V7 documentation |
| [CLAUDE.md](CLAUDE.md) | Claude agent instructions |
| [GEMINI.md](GEMINI.md) | Gemini agent instructions |
| [MISSION.md](MISSION.md) | ASI mission statement |
| [ROADMAP_NEXUS_V7.md](ROADMAP_NEXUS_V7.md) | Development roadmap |
| [SESSION_CONTINUITY.md](SESSION_CONTINUITY.md) | Session state |

## Commands

```bash
nexus> /help           # Show commands
nexus> /status         # Show state
nexus> /doctor         # System diagnostics
nexus> /evolve 3       # Create 3 children
nexus> /pool-stats     # DyLAN agent metrics
nexus> exit            # Quit
```

## Requirements

- **Python**: 3.13+
- **CLIs**: `gemini`, `claude` installed
- **OS**: Windows (tested), Linux/macOS (compatible)

## Contributing

NEXUS is an experimental research project. Contributions should:
1. Maintain alignment with KERNEL.py
2. Follow the evolution protocol
3. Pass all validation tests

## License

See [LICENSE](LICENSE) for details.

## Author

**Yann Abadie** - Creator and Alignment Authority

---

*"Toward Artificial Superintelligence through Darwinian Evolution"*
