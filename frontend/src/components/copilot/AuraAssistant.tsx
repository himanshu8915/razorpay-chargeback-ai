"use client";

import React, { useState, useEffect, useRef } from "react";
import { useMerchant } from "@/app/MerchantContext";
import { Send, Sparkles, User, Loader2, Bot } from "lucide-react";
import axios from "axios";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export default function AuraAssistant({ isVisible, toggleVisibility }: { isVisible: boolean, toggleVisibility: () => void }) {
  const { activeMerchantId } = useMerchant();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hello! I am Aura. I can help you analyze disputes, generate representments, or answer questions about your portfolio. How can I assist you today?",
      timestamp: new Date().toISOString()
    }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim() || !activeMerchantId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await axios.post("/api/v1/copilot/chat", {
        merchant_id: activeMerchantId,
        message: userMessage.content,
      });

      const assistantMessage: Message = {
        id: Date.now().toString() + "-ai",
        role: "assistant",
        content: res.data.response || "I processed that for you.",
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        id: Date.now().toString() + "-err",
        role: "assistant",
        content: "Sorry, my backend services are currently unavailable. Please ensure the database is running.",
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div className="w-80 border-l border-gray-200 bg-[#FAF9F6] flex flex-col h-full shadow-inner relative z-10 flex-shrink-0">
      {/* Header */}
      <div className="flex h-16 shrink-0 items-center justify-between px-4 border-b border-gray-200 bg-white shadow-sm z-20">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-amber-100 rounded-lg">
            <Sparkles className="h-5 w-5 text-amber-600" />
          </div>
          <span className="font-semibold text-gray-900 tracking-tight">Aura</span>
        </div>
        <button onClick={toggleVisibility} className="text-gray-400 hover:text-gray-600 text-sm font-medium">
          Hide
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
            <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${msg.role === "user" ? "bg-stone-200" : "bg-amber-100"}`}>
              {msg.role === "user" ? <User className="h-4 w-4 text-stone-600" /> : <Bot className="h-4 w-4 text-amber-600" />}
            </div>
            <div className={`flex max-w-[80%] rounded-2xl px-4 py-2 ${msg.role === "user" ? "bg-stone-800 text-white rounded-tr-sm" : "bg-white border border-stone-200 text-stone-800 rounded-tl-sm shadow-sm"}`}>
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center bg-amber-100">
              <Sparkles className="h-4 w-4 text-amber-600" />
            </div>
            <div className="flex max-w-[80%] rounded-2xl px-4 py-3 bg-white border border-stone-200 rounded-tl-sm shadow-sm">
              <Loader2 className="h-4 w-4 text-amber-600 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t border-gray-200">
        <div className="relative flex items-center">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask Aura..."
            className="w-full resize-none rounded-xl border border-stone-300 py-3 pl-4 pr-12 text-sm text-stone-900 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 bg-stone-50"
            rows={1}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="absolute right-2 p-2 rounded-lg bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
