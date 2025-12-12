import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from core.interface.commands.evolution import EvolveCommand, SpawnCommand
from core.interface.commands.misc import SpecializeCommand
from core.interface.commands.registry import CommandContext, CommandStatus

class TestCommandsIntegrity(unittest.TestCase):
    def setUp(self):
        self.mock_orchestrator = MagicMock()
        self.mock_console = MagicMock()
        self.mock_config = MagicMock()
        self.mock_repl = MagicMock()
        
        # Setup mock workspace path
        self.mock_config.workspace_path = Path("test_root/nexus_v7/workspace")
        # Ensure parent access works for logic that climbs up
        # workspace.parent -> nexus_v7
        # workspace.parent.parent -> test_root
        
        self.context = CommandContext(
            orchestrator=self.mock_orchestrator,
            console=self.mock_console,
            config=self.mock_config,
            extras={"repl": self.mock_repl}
        )

    def test_evolve_command_structure(self):
        """Verify /evolve command structure and delegation."""
        cmd = EvolveCommand()
        self.assertEqual(cmd.name, "/evolve")
        
        # Execute
        result = cmd.execute("3", self.context)
        
        # Should delegate to repl.run_evolve
        self.mock_repl.run_evolve.assert_called_with(child_count=3)
        self.assertEqual(result.status, CommandStatus.SUCCESS)

    def test_spawn_command_structure(self):
        """Verify /spawn command structure."""
        cmd = SpawnCommand()
        self.assertEqual(cmd.name, "/spawn")
        
        # We mock _spawn_agent to avoid actual file operations
        with patch.object(SpawnCommand, '_spawn_agent') as mock_spawn:
            result = cmd.execute("python expert", self.context)
            
            mock_spawn.assert_called_once()
            self.assertEqual(result.status, CommandStatus.SUCCESS)

    def test_specialize_command_structure(self):
        """Verify /specialize command structure."""
        cmd = SpecializeCommand()
        self.assertEqual(cmd.name, "/specialize")
        
        # We mock internal methods to avoid actual file operations/brainstorming
        with patch.object(SpecializeCommand, '_brainstorm_spinoff_with_ais') as mock_brainstorm:
            # Mock return of brainstorm
            mock_brainstorm.return_value = [{'file': 'test.py', 'change': 'fix'}]
            
            # Mock lineage functions (imported inside execute, so we patch the source)
            with patch('core.evolution.lineage.load_lineage') as mock_load_lineage, \
                 patch('core.evolution.lineage.get_current_parent') as mock_get_parent, \
                 patch('shutil.rmtree'), \
                 patch('shutil.copytree'), \
                 patch('shutil.copy2'), \
                 patch('pathlib.Path.mkdir'), \
                 patch('pathlib.Path.write_text'), \
                 patch('pathlib.Path.read_text', return_value="original content"), \
                 patch('pathlib.Path.exists', return_value=True): # Assume files exist for copy
                
                # Setup lineage mocks
                mock_load_lineage.return_value = {}
                mock_get_parent.return_value = {"id": "NEXUS_V7_PARENT"}

                result = cmd.execute("create a web server version", self.context)
                
                # It should succeed
                self.assertEqual(result.status, CommandStatus.SUCCESS, f"Command failed: {result.message}")
                mock_brainstorm.assert_called_once()

if __name__ == "__main__":
    unittest.main()
