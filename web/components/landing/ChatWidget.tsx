"use client";
import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Minimize2, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

type Message = {
  id: string;
  text: string;
  sender: 'user' | 'agent';
  timestamp: Date;
};

// API base URL - adjust based on environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize chat session when widget opens
  useEffect(() => {
    if (isOpen && !isConnected) {
      initializeSession();
    }
  }, [isOpen, isConnected]);

  // Auto-scroll to bottom
  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, isOpen]);

  const initializeSession = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/init`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        setIsConnected(true);
        setMessages([
          {
            id: '1',
            text: data.welcome_message,
            sender: 'agent',
            timestamp: new Date(),
          },
        ]);
      } else {
        // Fallback to simulated mode if API fails
        console.error('Failed to initialize chat session');
        setIsConnected(true);
        setMessages([
          {
            id: '1',
            text: 'Hello! How can I help you with Calleem today?',
            sender: 'agent',
            timestamp: new Date(),
          },
        ]);
      }
    } catch (error) {
      console.error('Error initializing chat:', error);
      // Fallback to simulated mode
      setIsConnected(true);
      setMessages([
        {
          id: '1',
          text: 'Hello! How can I help you with Calleem today?',
          sender: 'agent',
          timestamp: new Date(),
        },
      ]);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !isConnected) return;

    const userMessage = inputValue.trim();
    const newUserMessage: Message = {
      id: Date.now().toString(),
      text: userMessage,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newUserMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const agentResponse: Message = {
          id: (Date.now() + 1).toString(),
          text: data.response,
          sender: 'agent',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, agentResponse]);
        // Update session ID if returned
        if (data.session_id) {
          setSessionId(data.session_id);
        }
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Fallback response
      const agentResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: "I'm sorry, I'm having trouble connecting right now. Please try again or contact our support team directly.",
        sender: 'agent',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, agentResponse]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-4 font-manrope">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="w-[350px] h-[500px] bg-forest border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="bg-[#153629] p-4 flex justify-between items-center border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-[#2C7A44]' : 'bg-yellow-500 animate-pulse'}`}></div>
                  {isConnected && <div className="absolute inset-0 bg-[#2C7A44] rounded-full animate-ping opacity-20"></div>}
                </div>
                <div>
                  <h4 className="font-bold text-white text-sm">Calleem Support</h4>
                  <p className="text-xs text-white/50">{isConnected ? 'Online' : 'Connecting...'}</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-white/60 hover:text-white transition-colors"
                aria-label="Close chat"
              >
                <Minimize2 size={18} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#0e2e22] scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
              {!isConnected && (
                <div className="flex flex-col items-center justify-center h-full text-white/40 gap-2">
                  <Loader2 size={24} className="animate-spin" />
                  <span className="text-xs">Connecting to AI assistant...</span>
                </div>
              )}
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-3 rounded-2xl text-sm leading-relaxed ${msg.sender === 'user'
                        ? 'bg-leaf text-white rounded-tr-sm'
                        : 'bg-[#1d331a] border border-white/10 text-white/90 rounded-tl-sm'
                      }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-[#1d331a] border border-white/10 p-4 rounded-2xl rounded-tl-sm flex gap-1 items-center h-10">
                    <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce"></span>
                    <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce delay-100"></span>
                    <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce delay-200"></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleSendMessage} className="p-3 bg-[#153629] border-t border-white/5 flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={isConnected ? "Type a message..." : "Please wait..."}
                disabled={!isConnected}
                className="flex-1 bg-black/20 border border-white/5 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-[#2C7A44]/30 transition-colors disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || !isConnected}
                className="p-2.5 bg-[#2C7A44] text-white rounded-xl hover:bg-[#2C7A44]/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                aria-label="Send message"
              >
                <Send size={18} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Toggle Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className={`p-4 rounded-full shadow-lg flex items-center justify-center transition-all duration-300 ${isOpen
            ? 'bg-[#153629] text-white border border-white/10'
            : 'bg-[#2C7A44] text-white shadow-[0_0_20px_rgba(44,122,68,0.3)]'
          }`}
        aria-label="Toggle chat"
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} className="fill-current" />}
      </motion.button>
    </div>
  );
};

export default ChatWidget;