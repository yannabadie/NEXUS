import React from 'react';
import { ShoppingCart, Check, Shield, Code, Cpu } from 'lucide-react';

export interface AgentProduct {
  id: string;
  name: string;
  price: string;
  description: string;
  type: 'Quality' | 'Dev' | 'Security';
  capabilities: string[];
}

interface AgentCardProps {
  agent: AgentProduct;
  onInstall: (agent: AgentProduct) => void;
}

const AgentCard: React.FC<AgentCardProps> = ({ agent, onInstall }) => {
  const getIcon = (type: string) => {
    switch (type) {
      case 'Quality': return <Shield className="w-6 h-6 text-green-400" />;
      case 'Dev': return <Code className="w-6 h-6 text-blue-400" />;
      case 'Security': return <Cpu className="w-6 h-6 text-red-400" />;
      default: return <Cpu className="w-6 h-6 text-gray-400" />;
    }
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 hover:border-blue-500 transition-all shadow-lg hover:shadow-blue-500/20 group">
      <div className="flex justify-between items-start mb-4">
        <div className="p-3 bg-gray-700/50 rounded-lg group-hover:bg-blue-500/20 transition-colors">
          {getIcon(agent.type)}
        </div>
        <span className="bg-blue-900/40 text-blue-300 text-xs px-2 py-1 rounded font-mono">
          {agent.price}
        </span>
      </div>
      
      <h3 className="text-xl font-bold text-white mb-2">{agent.name}</h3>
      <p className="text-gray-400 text-sm mb-4 h-10">{agent.description}</p>
      
      <div className="space-y-2 mb-6">
        {agent.capabilities.map((cap, idx) => (
          <div key={idx} className="flex items-center text-xs text-gray-500">
            <Check className="w-3 h-3 mr-2 text-green-500" />
            {cap}
          </div>
        ))}
      </div>

      <button
        onClick={() => onInstall(agent)}
        className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-500 text-white rounded-lg flex items-center justify-center space-x-2 transition-colors font-medium"
        data-testid={`install-${agent.id}`}
      >
        <ShoppingCart className="w-4 h-4" />
        <span>Install Agent</span>
      </button>
    </div>
  );
};

export default AgentCard;
