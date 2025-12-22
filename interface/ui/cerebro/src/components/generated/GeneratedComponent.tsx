import React from 'react';
            import { clsx } from 'clsx';

            export default function GeneratedComponent() {
                return (
                    <div className="p-8 bg-nexus-darker min-h-full text-white animate-fade-in">
                        <div className="mb-6 flex items-center space-x-2 opacity-50 hover:opacity-100 transition-opacity">
                            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                            <span className="text-xs font-mono text-primary">&lt;GeneratedComponent /&gt;</span>
                        </div>
                        I see this is a context file for the **CEREBRO UI Designer** - a UI generation agent for NEXUS. This appears to be a specialized agent prompt that's being used to generate React components for the Cerebro interface.

Looking at the git status, I can see several UI-related files:
- `interface/ui/cerebro/src/pages/GenerativeCanvas.tsx` (new)
- `interface/ui/cerebro/src/components/generated/` (new directory)
- `core/ui/generator.py` (new)
- `core/prompts/ui_designer.md` (new)

This seems to be part of implementing **generative UI capabilities** for NEXUS's Cerebro interface.

## What would you like me to help with?

Based on the context, I can help with:

1. **Review the UI Designer implementation** - Check the `generator.py` and prompt structure
2. **Test the generative UI system** - Verify components are being generated correctly
3. **Improve the UI Designer agent** - Enhance the prompt or generation logic
4. **Document the Generative UI feature** - Add to ROADMAP/documentation
5. **Debug any issues** - If there are problems with the current implementation

What specific task would you like me to work on? Or would you like me to analyze the current state of the generative UI implementation?
                    </div>
                );
            }