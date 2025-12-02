import json

mutation_2 = {
    "file": "core/orchestration_v7.py",
    "action": "append",
    "change": """

class CycleDetector:
    """Detects ping-pong cycles in agent conversation."""
    
    def __init__(self, buffer_size: int = 30, cycle_threshold: int = 2):
        self.buffer_size = buffer_size
        self.cycle_threshold = cycle_threshold
        self.hash_buffer: list = []
    
    def _hash_message(self, msg: str) -> str:
        """Create a normalized hash of message content."""
        import hashlib
        # Normalize: lowercase, remove whitespace, take first 500 chars
        normalized = msg.lower().replace(' ', '').replace('\n', '')[:500]
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def check_cycle(self, message: str) -> bool:
        """Check if this message creates a cycle. Returns True if cycle detected."""
        msg_hash = self._hash_message(message)
        
        # Count occurrences of this hash in buffer
        occurrences = self.hash_buffer.count(msg_hash)
        
        # Add to buffer
        self.hash_buffer.append(msg_hash)
        if len(self.hash_buffer) > self.buffer_size:
            self.hash_buffer.pop(0)
        
        return occurrences >= self.cycle_threshold
    
    def reset(self):
        """Clear the hash buffer."""
        self.hash_buffer.clear()
""",
    "reason": "Ajoute détection de cycles ping-pong via hash rolling buffer pour éviter les boucles infinies entre agents",
    "expected_asi_impact": 0.05
}

mutation_3 = {
    "file": "core/drivers/gemini_driver_v7.py",
    "action": "replace",
    "target": "        import re",
    "change": "''')        import re

        # 0. NEW: Try to find JSON array (for evolution mutations)
        array_block_pattern = r'```json\s*(\[.*?\])\s*```'
        array_matches = re.findall(array_block_pattern, text, re.DOTALL)
        if array_matches:
            for match in reversed(array_matches):
                try:
                    parsed = json.loads(match)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        # Return as wrapper dict for compatibility
                        return {"_json_array": parsed, "_is_mutation_list": True}
                except json.JSONDecodeError:
                    continue''',
    "reason": "Ajoute extraction de listes JSON [{},...] pour les mutations d'évolution, avant le pattern objet standard",
    "expected_asi_impact": 0.02
}

mutations = [mutation_2, mutation_3]

with open('mutation.json', 'w', encoding='utf-8') as f:
    json.dump(mutations, f, indent=2, ensure_ascii=False)

print("mutation.json generated successfully.")