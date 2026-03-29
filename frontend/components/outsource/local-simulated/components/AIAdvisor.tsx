import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, Send, X } from 'lucide-react';
import { askCopilot } from '../backendClient';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Props {
  simulationData: any;
  simulationResult: any;
  onClose: () => void;
}

const AIAdvisor = ({ simulationData, simulationResult, onClose }: Props) => {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "I am your AI Corrosion Advisor. Based on your current simulation, I can provide specific material optimizations, maintenance schedules, or regulatory compliance advice. How can I assist you today?" }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const prompt = `You are a world-class AI Corrosion Engineering Advisor.
      Current Project Context:
      Material: ${simulationData?.material || 'Unknown'}
      Structure: ${simulationData?.structure || 'Unknown'}
      Environment: Temp ${simulationData?.temperature} C, Humidity ${simulationData?.humidity}%, Salinity ${simulationData?.salinity}g/L, pH ${simulationData?.pH}.
      Simulation Results: Risk Score ${simulationResult?.riskScore}/100, Predicted Lifespan ${simulationResult?.predictedLifespan} years.
      Financial Signals: CAPEX ${simulationResult?.capexRequirement || 'n/a'}, ROI ${simulationResult?.projectedROI || 'n/a'}, ESG ${simulationResult?.esgCompliance || 'n/a'}.
      Conversation Context: ${messages.slice(-4).map((m) => `${m.role}: ${m.content}`).join(' | ')}
      
      User Question: ${userMessage}
      
      Provide a highly technical, authoritative, and actionable response. Focus on material intelligence, financial risk mitigation, and ESG compliance.
      Keep response to 5 bullet points max.`;

      const response = await askCopilot(prompt);

      setMessages(prev => [...prev, { role: 'assistant', content: response || 'I apologize, but I encountered an error processing your request.' }]);
    } catch (error) {
      console.error('AI Advisor Error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: "System error. Please verify your connection and try again." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ x: 400, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 400, opacity: 0 }}
      className="fixed right-8 top-24 bottom-24 w-96 glass border border-white/10 z-50 flex flex-col shadow-2xl shadow-black/50"
    >
      {/* Header */}
      <div className="p-6 border-b border-white/10 flex items-center justify-between bg-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center border border-accent/40">
            <Bot className="w-6 h-6 text-accent" />
          </div>
          <div>
            <h3 className="text-lg font-display font-black text-white uppercase tracking-tighter">AI Advisor</h3>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              <span className="text-[8px] font-mono font-bold text-white/40 uppercase tracking-widest">Neural Engine Active</span>
            </div>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors">
          <X className="w-5 h-5 text-white/40" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        {messages.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[85%] p-4 rounded-2xl text-xs font-medium leading-relaxed ${
              msg.role === 'user' 
                ? 'bg-accent text-bg rounded-tr-none' 
                : 'bg-white/5 border border-white/10 text-white/80 rounded-tl-none'
            }`}>
              {msg.content}
            </div>
          </motion.div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white/5 border border-white/10 p-4 rounded-2xl rounded-tl-none flex gap-1">
              <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:-0.3s]" />
              <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:-0.15s]" />
              <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" />
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="p-4 border-t border-white/5 flex gap-2 overflow-x-auto custom-scrollbar no-scrollbar">
        {['Optimize Material', 'Maintenance Plan', 'ESG Impact'].map((action) => (
          <button
            key={action}
            onClick={() => {
              setInput(action);
              // handleSend(); // We'll let the user click send to confirm
            }}
            className="whitespace-nowrap px-3 py-1.5 bg-white/5 border border-white/10 rounded-full text-[10px] font-mono font-bold text-white/60 hover:border-accent hover:text-accent transition-all"
          >
            {action}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="p-6 bg-white/5">
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about material intelligence..."
            className="w-full p-4 pr-12 bg-black/40 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-accent transition-all"
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-accent disabled:opacity-20 transition-opacity"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default AIAdvisor;
