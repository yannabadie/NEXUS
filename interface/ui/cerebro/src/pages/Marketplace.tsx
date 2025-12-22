import React, { useState } from 'react';
import AgentCard, { AgentProduct } from '../components/Marketplace/AgentCard';
import { Search } from 'lucide-react';

const MOCK_AGENTS: AgentProduct[] = [
    {
        id: 'qa_sentinel',
        name: 'QA Sentinel',
        price: '$50/mo',
        description: 'Autonomous Quality Assurance. Runs Pytest & Vitest 24/7.',
        type: 'Quality',
        capabilities: ['Automated Testing', 'Regression Detection', 'Report Generation']
    },
    {
        id: 'python_dev',
        name: 'Python Specialist',
        price: '$20/mo',
        description: 'Expert in Python 3.13, AsyncIO, and FSM architecture.',
        type: 'Dev',
        capabilities: ['Code Generation', 'Refactoring', 'Bug Fixing']
    },
    {
        id: 'security_audit',
        name: 'SecOps Guardian',
        price: '$100/mo',
        description: 'Enterprise grade security scanning and vulnerability patching.',
        type: 'Security',
        capabilities: ['Vulnerability Scan', 'Dependency Audit', 'Access Control']
    }
];

const Marketplace: React.FC = () => {
    const [searchTerm, setSearchTerm] = useState('');

    const handleInstall = (agent: AgentProduct) => {
        // In a real app, this would call the API
        console.log(`Installing ${agent.name}...`);
        alert(`Request sent: Installing ${agent.name}`);
    };

    const filteredAgents = MOCK_AGENTS.filter(agent =>
        agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        agent.type.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="p-8 min-h-screen bg-gray-900 text-white">
            <div className="max-w-7xl mx-auto">
                <header className="mb-12 text-center">
                    <h1 className="text-4xl font-extrabold mb-4 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                        NEXUS Agent Marketplace
                    </h1>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                        Discover and deploy specialized intelligence to upgrade your Swarm.
                        Enhance your capabilities instantly.
                    </p>
                </header>

                <div className="mb-8 relative max-w-md mx-auto">
                    <Search className="absolute left-3 top-3 text-gray-500 w-5 h-5" />
                    <input
                        type="text"
                        placeholder="Search agents..."
                        className="w-full bg-gray-800 border border-gray-700 rounded-full py-2 pl-10 pr-4 text-gray-300 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {filteredAgents.map(agent => (
                        <AgentCard
                            key={agent.id}
                            agent={agent}
                            onInstall={handleInstall}
                        />
                    ))}
                </div>

                {filteredAgents.length === 0 && (
                    <div className="text-center text-gray-500 mt-12">
                        No agents found matching "{searchTerm}"
                    </div>
                )}
            </div>
        </div>
    );
};

export default Marketplace;
