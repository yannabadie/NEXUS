# Implementation Plan - Agent Marketplace

## 1. Component Structure
- `AgentCard.tsx`: Display agent Name, Price, Capabilities, and "Install" button.
- `Marketplace.tsx`: Grid layout of available agents.

## 2. Mock Data
Since we don't have a backend DB yet, we will mock the agent list:
```typescript
const AVAILABLE_AGENTS = [
  { id: 'qa_sentinel', name: 'QA Sentinel', price: '$50/mo', type: 'Quality' },
  { id: 'python_dev', name: 'Python Specialist', price: '$20/mo', type: 'Dev' },
  { id: 'security_guard', name: 'Security Auditor', price: '$100/mo', type: 'Sec' }
]
```

## 3. Integration
- Add "Marketplace" to the main Navigation (Sidebar/Header).
- Integrate with `App.tsx` routing.
