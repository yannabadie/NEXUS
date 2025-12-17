# NEXUS Evolution Guide - User Manual

**Version**: 1.0
**Target Audience**: NEXUS Users
**Last Updated**: 2025-11-21

---

## Quick Start

### Basic Evolution Cycle

```bash
# 1. Check current status
nexus7> /evolve-status

# 2. Trigger evolution (3 children)
nexus7> /evolve 3

# 3. Review children after benchmarks complete
nexus7> /review

# 4. Approve best child
[A]pprove | [R]eject
> A
```

---

## Use Cases

### Use Case 1: Manual Performance Optimization

**Scenario**: You notice NEXUS has high latency on complex tasks.

**Steps**:
1. Trigger evolution with 3 children focused on performance
2. Wait 48h for evaluation (recommended timeline)
3. Review children ASI scores
4. Approve child with best performance metrics
5. New parent becomes active

**Example**:
```bash
nexus7> /evolve 3
# Wait for "EVOLUTION CYCLE COMPLETE"
# Check email notification or PENDING_REVIEW.md

nexus7> /review
Child 1/3: NEXUS_V7.1_CHILD_001
ASI Score: 0.78 (+4.0% vs parent)
Improvements: Optimized FSM state transitions
> A  # Approve

# Child promoted, NEXUS reboots with V6.1
```

### Use Case 2: Auto-Evolution After Heavy Usage

**Scenario**: You've used NEXUS for 50 successful tasks.

**Automatic**:
- NEXUS auto-triggers evolution
- Creates 3 children automatically
- Notifies you via email + PENDING_REVIEW.md
- You review when convenient

**Example**:
```bash
nexus7> [Working on task 50...]
� AUTO-EVOLUTION TRIGGER: 50 successful turns reached
   Starting evolution cycle...
[Evolution runs in background]
 EVOLUTION CYCLE COMPLETE
Use /review to evaluate children
```

### Use Case 3: Stagnation Recovery

**Scenario**: 3 generations without improvement - SURVIVAL_LAW triggered.

**Steps**:
1. Check stagnation status: `/evolve-status`
2. If counter = 3/3, human intervention required
3. Options:
   - Design custom mutations manually
   - Request architectural change
   - Rollback to previous generation
   - Force mutation injection

**Example**:
```bash
nexus7> /evolve-status
Stagnation Counter: 3/3
=� CRITICAL: SURVIVAL_LAW triggered

# Option A: Custom mutation
nexus7> /evolve-custom --mutation="rewrite_memory_system"

# Option B: Rollback
nexus7> /rollback GEN_005
```

---

## Workflows

### Workflow 1: Routine Maintenance Evolution

**Frequency**: Every 50 successful tasks (auto) or weekly (manual)

```
Week 1: Use NEXUS normally
Week 2: /evolve 3 � Review � Approve best
Week 3: Use improved NEXUS
Week 4: Repeat
```

### Workflow 2: Targeted Feature Addition

**Scenario**: You need NEXUS to handle a new type of task better.

```
1. Identify bottleneck (e.g., "Poor at data analysis")
2. Design mutation: enhance_data_analysis_prompt()
3. Create child with custom mutation
4. Evaluate on data analysis benchmarks
5. Promote if superior
```

**Code Example**:
```python
from core.evolution.mutator import create_child

def enhance_data_analysis(child_path, **kwargs):
    # Add pandas/numpy optimization
    prompt_file = child_path / "prompts/system_claude_v7.md"
    with open(prompt_file, 'a') as f:
        f.write("\n\n## Data Analysis Expertise\n...")
    return {"files_modified": [str(prompt_file)], "lines_changed": 50}

result = create_child(
    parent_path=Path("NEXUS_V7_CHRYSALIS"),
    child_id="NEXUS_V7.1_DATA_ANALYSIS",
    mutation_functions=[enhance_data_analysis],
    ...
)
```

### Workflow 3: A/B Testing Parent vs Child

**Use Case**: Unsure if child is actually better.

```
1. Create child with optimization
2. Run both parent & child in parallel on same tasks
3. Compare performance metrics manually
4. Promote child if confirmed superior
```

---

## Best Practices

### Do's 

1. **Wait 48h before reviewing** - Recommended evaluation timeline
2. **Review all children** - Don't skip, even if one looks good
3. **Test children before approval** - Use [T]est option in /review
4. **Document custom mutations** - Add detailed justifications
5. **Monitor stagnation counter** - Check /evolve-status regularly
6. **Backup before promotion** - Git commit parent state
7. **Read birth certificates** - Understand what changed
8. **Check ASI score breakdown** - Not just total score

### Don'ts L

1. **Don't rush promotion** - Minimum 24h evaluation
2. **Don't ignore regressions** - Child with lower ASI = reject
3. **Don't bypass review** - Human validation mandatory
4. **Don't delete PENDING_REVIEW early** - Keep for audit trail
5. **Don't modify birth certificates** - Immutable records
6. **Don't exceed rate limits** - Max 3 generations/day
7. **Don't ignore SURVIVAL_LAW** - Stagnation = serious issue
8. **Don't skip backups** - Always git commit before promotion

---

## Troubleshooting

### Issue: "Evolution taking too long"

**Cause**: Benchmarks running (simulated or real)

**Solution**:
- MVP: Simulated benchmarks take ~2-3 seconds per child
- Production: Real benchmarks may take minutes
- Check background process: `ps aux | grep asi_proximity`

### Issue: "No improvement after 3 generations"

**Cause**: SURVIVAL_LAW triggered

**Solution**:
1. Review mutation strategies (too conservative?)
2. Try different optimization areas (FSM � memory � prompts)
3. Request human-designed mutations
4. Consider architectural change (FSM � Actor Model)

### Issue: "Child approved but not active"

**Cause**: Auto-promotion not yet implemented (MVP)

**Solution**:
- Manual promotion:
```bash
cd GENERATION_ACTIVE/NEXUS_V7.1_CHILD_001
# Move to production location
# Update LINEAGE.json manually
# Reboot NEXUS
```

### Issue: "Email notifications not working"

**Cause**: `.env` not configured

**Solution**:
```bash
cp .env.template .env
nano .env  # Add NEXUS_EMAIL_PASSWORD
# Restart NEXUS
```

---

## FAQs

**Q: How often should I evolve NEXUS?**
A: Auto-evolution triggers every 50 successful tasks. Manual evolution can be done anytime, but respect rate limits (3 gen/day).

**Q: What if all children are worse than parent?**
A: Parent wins by default. Children archived. Stagnation counter increments.

**Q: Can I create more than 3 children?**
A: Yes, use `/evolve 10` (if in stable mode after 5 successful generations). MVP limit is 3.

**Q: How do I know if a child is ready for review?**
A: Check email, PENDING_REVIEW.md file, or boot NEXUS (alert displays).

**Q: Can I rollback a bad promotion?**
A: Yes, use `/rollback GEN_XXX` to restore previous generation.

**Q: What happens to rejected children?**
A: Archived to `ARCHIVE/GEN_XXX/candidates/` for future reference.

**Q: How are ASI scores calculated?**
A: Weighted average: Coding (30%) + Reasoning (30%) + Creativity (25%) + Scalability (15%).

**Q: Can I customize mutation functions?**
A: Yes, write Python functions matching the mutation API (see API_REFERENCE.md).

---

## Advanced Topics

### Custom Mutations

Create custom mutation functions:

```python
def my_custom_optimization(child_path: Path, **kwargs) -> Dict:
    """
    Custom mutation example.

    Args:
        child_path: Path to child NEXUS
        **kwargs: Custom parameters

    Returns:
        dict: Mutation result metadata
    """
    # Your mutation logic here
    target = child_path / "core/custom.py"

    # Modify files
    with open(target, 'w') as f:
        f.write("# Optimized code")

    # Return metadata
    return {
        "files_modified": [str(target)],
        "lines_changed": 100,
        "optimization_type": "Custom"
    }
```

### Benchmark Customization

Replace simulated benchmarks with real tests:

```python
# benchmarks/asi_proximity.py
def run_coding_benchmark(nexus_path):
    # Real coding tasks
    results = []
    for task in coding_tasks:
        score = nexus.solve(task)
        results.append(score)
    return sum(results) / len(results)
```

### Multi-Objective Optimization

Optimize for multiple goals:

```python
expected_improvements = {
    "latency_reduction": "15%",
    "memory_efficiency": "10%",
    "accuracy_increase": "5%"
}
```

---

## References

- **core/evolution/README.md** - Complete module documentation
- **NEXUS_V7_CHRYSALIS/README.md** - Main NEXUS documentation
- **EVOLUTION_PROTOCOL.md** - Detailed protocol specification
- **API_REFERENCE.md** - Function signatures and parameters
- **INVARIANTS.md** - Five immutable laws
- **MISSION.md** - NEXUS vision and ASI objective

---

## Support

- **Email**: yann.abadie@outlook.com
- **GitHub**: https://github.com/yannabadie/NEXUS
- **Branch**: N7C (development)
- **Issues**: https://github.com/yannabadie/NEXUS/issues
