"use client";
import React from 'react';
import { motion } from 'framer-motion';
import { Check, X } from 'lucide-react';

const Comparison: React.FC = () => {
    const traditional = [
        "Messy calendars, manual scheduling",
        "Missed calls, no follow-ups",
        "Limited automation, double bookings",
        "After-hours queries go unanswered",
        "Generic support, slow replies"
    ];

    const calleem = [
        "Smart dashboard, real-time tracking",
        "Voice AI Call Handling",
        "Automated booking & reminders",
        "24/7 support and handling calls",
        "Priority support, fast response"
    ];

    return (
        <section className="py-24 px-5 bg-sage relative">
            {/* Background decoration */}
            <div className="absolute inset-0 bg-sage z-0"></div>

            <div className="max-w-[1000px] mx-auto relative z-10">
                <div className="flex flex-col items-center gap-6 mb-20 text-center">
                    <div className="bg-transparent border border-none shadow-none">
                        <span className="flex items-center gap-2 text-[#184a27] font-semibold tracking-wide bg-transparent">
                            <span className="w-2 h-2 rounded-full bg-[#1e5438]"></span>
                            Why Calleem?
                        </span>
                    </div>
                    <h2 className="text-3xl md:text-5xl font-manrope font-bold max-w-2xl text-white">
                        There's a smarter way to manage appointments
                    </h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-0 md:gap-0 rounded-[30px] overflow-hidden bg-forest shadow-2xl">
                    {/* Traditional Column */}
                    <div className="p-8 md:p-12 flex flex-col gap-8 bg-forest">
                        <h5 className="text-xl font-bold font-manrope text-white/40 mb-2">Traditional Methods</h5>
                        <div className="flex flex-col gap-6">
                            {traditional.map((item, i) => (
                                <div key={i} className="flex items-start gap-3 opacity-50">
                                    <div className="mt-1 min-w-[16px]"><X size={16} /></div>
                                    <p className="text-base md:text-lg font-manrope font-medium">{item}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Calleem Column */}
                    <motion.div
                        initial={{ opacity: 0, x: 50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.7 }}
                        className="p-8 md:p-12 flex flex-col gap-8 bg-white/10 md:bg-[#648768] relative shadow-[inset_0px_1px_0px_0px_rgba(44,122,68,0.3)]"
                    >
                        <div className="flex items-center gap-3 mb-2">
                            <svg className="w-8 h-6 text-white" viewBox="0 0 41 24" fill="currentColor">
                                <path d="M 21.821 0.929 C 22.354 0.38 23.092 0.068 23.865 0.065 L 33.762 0.065 C 40.198 0.065 43.42 8.011 38.869 12.659 L 28.958 22.783 C 28.503 23.247 27.725 22.918 27.725 22.26 L 27.725 13.345 L 28.87 12.174 C 29.78 11.245 29.136 9.656 27.848 9.656 L 13.276 9.656 L 21.821 0.929 Z" fill="currentColor"></path>
                                <path d="M 19.179 22.071 C 18.646 22.62 17.908 22.932 17.135 22.935 L 7.238 22.935 C 0.802 22.935 -2.42 14.988 2.131 10.341 L 12.042 0.217 C 12.497 -0.247 13.276 0.082 13.276 0.739 L 13.276 9.655 L 12.13 10.825 C 11.22 11.755 11.864 13.344 13.152 13.344 L 27.724 13.344 L 19.178 22.071 Z" fill="currentColor"></path>
                            </svg>
                            <span className="text-xl font-bold">Calleem</span>
                        </div>
                        <div className="flex flex-col gap-6">
                            {calleem.map((item, i) => (
                                <div key={i} className="flex items-start gap-3">
                                    <div className="mt-1 min-w-[16px] text-[#2C7A44]"><Check size={16} strokeWidth={4} /></div>
                                    <p className="text-base md:text-lg font-manrope font-semibold">{item}</p>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                </div>
            </div>
        </section>
    );
};

export default Comparison;