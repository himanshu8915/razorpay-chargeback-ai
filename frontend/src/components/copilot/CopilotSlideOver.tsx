"use client";

import React, { useState } from "react";
import axios from "axios";
import { MessageSquare, X, Send, Bot, User } from "lucide-react";
import { useMerchant } from "@/app/MerchantContext";
import { useParams } from "next/navigation";

export default function CopilotSlideOver({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { activeMerchantId } = useMerchant();
  const params = useParams();
  const caseId = params?.caseId as string | undefined;

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "assistant", content: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !activeMerchantId) return;

    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const res = await axios.post("/api/v1/copilot/chat", {
        message: userMessage,
        merchant_id: activeMerchantId,
        case_id: caseId || null,
        history: messages
      });
      
      setMessages(prev => [...prev, { role: "assistant", content: res.data.reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`fixed inset-y-0 right-0 z-50 flex w-96 flex-col bg-white shadow-2xl transition-transform transform ${isOpen ? "translate-x-0" : "translate-x-full"}`}>
      <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 bg-blue-600">
        <div className="flex items-center text-white">
          <Bot className="w-5 h-5 mr-2" />
          <h2 className="text-lg font-semibold tracking-tight">Copilot</h2>
        </div>
        <button onClick={onClose} className="text-white hover:text-blue-100">
          <X className="w-6 h-6" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-10 text-sm">
            <Bot className="w-10 h-10 mx-auto text-gray-300 mb-2" />
            <p>I am your Dispute Intelligence Copilot.</p>
            <p className="mt-1">
              {caseId 
                ? `Ask me anything about case ${caseId}.` 
                : `Ask me anything about ${activeMerchantId}'s portfolio.`}
            </p>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-lg px-4 py-2 text-sm ${
              msg.role === "user" 
                ? "bg-blue-600 text-white" 
                : "bg-white border border-gray-200 text-gray-800 shadow-sm"
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-lg px-4 py-2 text-sm bg-white border border-gray-200 shadow-sm flex items-center space-x-1">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-white border-t border-gray-200">
        <form onSubmit={sendMessage} className="flex space-x-2">
          <input
            type="text"
            className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm py-2 px-3 border bg-white text-gray-900"
            placeholder="Ask a question..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="inline-flex items-center justify-center rounded-md bg-blue-600 p-2 text-white shadow-sm hover:bg-blue-500 disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
