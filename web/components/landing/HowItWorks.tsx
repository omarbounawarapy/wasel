"use client";
import React from 'react';
import { motion } from 'framer-motion';
import { Play } from 'lucide-react';
import CallPipelineBox from '@/components/landing/CallPipelineBox';

const HowItWorks: React.FC = () => {
    return (
        <section id="how-it-works" className="py-24 px-5 bg-sage relative overflow-hidden">
            <div className="max-w-[1200px] mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, x: -50 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="flex flex-col md:flex-row md:items-center gap-6 mb-12"
                >
                    <div className="bg-[#e4ebdd] bg-opacity-10 backdrop-blur-md rounded-full pl-1 pr-6 py-1 flex items-center gap-3 w-fit border border-white/10">
                        <div className="bg-white rounded-full p-2">
                            <Play size={14} className="text-[#2C7A44] fill-[#2C7A44] ml-0.5" />
                        </div>
                        <span className="text-[#143d15] font-bold text-sm tracking-wide">Watch video</span>
                    </div>
                    <h2 className="text-3xl md:text-5xl font-host font-bold text-white leading-tight">
                        How Calleem works
                    </h2>
                </motion.div>

                {/* Video Card */}
                <motion.div
                    initial={{ opacity: 0, y: 50 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="w-full rounded-[30px] overflow-hidden shadow-2xl relative p-5 sm:p-8"
                    style={{ background: "#0e2e22" }}
                >
                    <CallPipelineBox />
                </motion.div>
            </div>
        </section>
    );
};

export default HowItWorks;