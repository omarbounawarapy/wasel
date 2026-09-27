"use client";
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Check, ChevronDown, ChevronUp, Settings2, Info } from 'lucide-react';

const Pricing: React.FC = () => {
    // Usage State
    const [calls, setCalls] = useState(500);
    const [duration, setDuration] = useState(3);
    // Helper component for owner-only UI — always hidden; admin view is not exposed to clients
    const AdminView = ({ children }: { children: React.ReactNode }) => {
        void children;
        return null;
    };

    // Cost Assumptions State
    const [costPerMinute, setCostPerMinute] = useState(0.082); // Combined var cost
    const [costPerCallFixed, setCostPerCallFixed] = useState(0.10); // Fixed per call overhead
    const [fixedInfraCost, setFixedInfraCost] = useState(30); // Monthly infra
    const [targetMargin, setTargetMargin] = useState(40); // Target Margin %

    const [showAnalysis, setShowAnalysis] = useState(false);

    const [financials, setFinancials] = useState({
        revenue: 0,
        totalCost: 0,
        variableCost: 0,
        profit: 0,
        margin: 0
    });

    useEffect(() => {
        // 1. Calculate Costs
        const variableCost = calls * (costPerCallFixed + (duration * costPerMinute));
        const totalCost = variableCost + fixedInfraCost;

        // 2. Calculate Revenue based on Target Margin
        let marginDecimal = targetMargin / 100;
        if (marginDecimal >= 0.95) marginDecimal = 0.95; // Cap at 95% to prevent infinity

        let rawRevenue = totalCost / (1 - marginDecimal);

        // 3. Round to "Nice" Price
        let displayPrice = Math.ceil(rawRevenue / 10) * 10 - 1;

        // Floor price safety
        const minPrice = Math.ceil((fixedInfraCost * 1.5) / 10) * 10 - 1;
        if (displayPrice < minPrice) displayPrice = minPrice;

        // 4. Recalculate Actuals based on rounded price
        const profit = displayPrice - totalCost;
        const margin = (profit / displayPrice) * 100;

        setFinancials({
            revenue: displayPrice,
            totalCost,
            variableCost,
            profit,
            margin
        });

    }, [calls, duration, costPerMinute, costPerCallFixed, fixedInfraCost, targetMargin]);

    const isEnterprise = calls > 4500;

    return (
        <section id="pricing" className="py-24 px-5 bg-sage relative overflow-hidden">
            <div className="max-w-[1000px] mx-auto relative z-10">
                <div className="text-center mb-12 space-y-6">
                    <span className="inline-block text-[#184a27] font-semibold tracking-wide">
                        <span className="flex items-center justify-center gap-2 text-[#2C7A44] font-medium">
                            <span className="w-2 h-2 rounded-full bg-[#2C7A44] shadow-[0_0_10px_#2C7A44]"></span>
                            Pricing Model
                        </span>
                    </span>
                    <h2 className="text-4xl md:text-5xl font-manrope font-bold">Transparent Pricing</h2>
                    <p className="text-white/60 text-lg max-w-lg mx-auto">
                        Interactive pricing that adapts to your scale. Adjust the parameters below to see how our model works.
                    </p>
                </div>

                <div className="bg-[#153629] rounded-[30px] border border-white/5 p-8 md:p-12 shadow-2xl transition-all duration-500">
                    <div className="flex flex-col lg:flex-row gap-12 lg:gap-16">

                        {/* Sliders Section */}
                        <div className="flex-1 flex flex-col justify-center gap-10">

                            {/* Calls Slider */}
                            <div className="space-y-6">
                                <div className="flex justify-between items-end">
                                    <label className="text-lg font-bold text-white">Monthly Calls</label>
                                    <div className="text-3xl font-host font-bold text-[#2C7A44]">{calls.toLocaleString()}</div>
                                </div>
                                <div className="relative h-4 bg-black/20 rounded-full border border-white/5">
                                    <input
                                        type="range"
                                        min="100"
                                        max="5000"
                                        step="100"
                                        value={calls}
                                        onChange={(e) => setCalls(Number(e.target.value))}
                                        className="absolute w-full h-full opacity-0 cursor-pointer z-10"
                                    />
                                    <div
                                        className="absolute top-0 left-0 h-full bg-[#2C7A44] rounded-full pointer-events-none transition-all duration-150 ease-out shadow-[0_0_15px_rgba(44,122,68,0.3)]"
                                        style={{ width: `${(calls / 5000) * 100}%` }}
                                    ></div>
                                    <div
                                        className="absolute top-1/2 -translate-y-1/2 w-6 h-6 bg-white rounded-full shadow-lg pointer-events-none transition-all duration-150 ease-out border-2 border-[#2C7A44]"
                                        style={{ left: `calc(${(calls / 5000) * 100}% - 12px)` }}
                                    ></div>
                                </div>
                                <div className="flex justify-between text-xs text-white/40 font-mono uppercase tracking-wider">
                                    <span>100 Calls</span>
                                    <span>5,000+ Calls</span>
                                </div>
                            </div>

                            {/* Duration Slider */}
                            <div className="space-y-6">
                                <div className="flex justify-between items-end">
                                    <label className="text-lg font-bold text-white flex items-center gap-2">
                                        Avg. Duration
                                    </label>
                                    <div className="text-3xl font-host font-bold text-[#2C7A44]">{duration} <span className="text-lg text-white/60">min</span></div>
                                </div>
                                <div className="relative h-4 bg-black/20 rounded-full border border-white/5">
                                    <input
                                        type="range"
                                        min="1"
                                        max="15"
                                        step="0.5"
                                        value={duration}
                                        onChange={(e) => setDuration(Number(e.target.value))}
                                        className="absolute w-full h-full opacity-0 cursor-pointer z-10"
                                    />
                                    <div
                                        className="absolute top-0 left-0 h-full bg-[#2C7A44] rounded-full pointer-events-none transition-all duration-150 ease-out shadow-[0_0_15px_rgba(44,122,68,0.3)]"
                                        style={{ width: `${(duration / 15) * 100}%` }}
                                    ></div>
                                    <div
                                        className="absolute top-1/2 -translate-y-1/2 w-6 h-6 bg-white rounded-full shadow-lg pointer-events-none transition-all duration-150 ease-out border-2 border-[#2C7A44]"
                                        style={{ left: `calc(${(duration / 15) * 100}% - 12px)` }}
                                    ></div>
                                </div>
                                <div className="flex justify-between text-xs text-white/40 font-mono uppercase tracking-wider">
                                    <span>1 min</span>
                                    <span>15 min</span>
                                </div>
                            </div>

                        </div>

                        {/* Dynamic Plan Card */}
                        <div className="lg:w-[400px]">
                            <motion.div
                                layout
                                className="bg-forest border border-[#2d4732] rounded-[24px] p-8 flex flex-col gap-6 h-full relative overflow-hidden shadow-2xl"
                            >
                                {/* Dynamic Background Glow */}
                                <div className="absolute -top-10 -right-10 w-40 h-40 bg-[#2C7A44]/20 blur-[80px] rounded-full pointer-events-none"></div>

                                <div className="relative z-10 flex flex-col h-full">
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className="text-2xl font-bold font-manrope text-white">{isEnterprise ? "Enterprise" : "Smart Plan"}</h3>
                                        <span className="bg-[#2C7A44]/10 text-[#2C7A44] border border-[#2C7A44]/20 text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wider">
                                            Auto-Scaling
                                        </span>
                                    </div>
                                    <p className="text-white/50 text-sm mb-6">
                                        {isEnterprise
                                            ? "High volume detected. Contact us for custom SLA."
                                            : "Dynamic pricing that scales with your usage."}
                                    </p>

                                    <div className="flex items-baseline gap-1 mb-8">
                                        <h2 className="text-6xl font-bold font-manrope tracking-tighter text-white">
                                            ${financials.revenue}
                                        </h2>
                                        <span className="text-white/40 font-medium">/mo</span>
                                    </div>

                                    <div className="space-y-4 mb-8">
                                        {[
                                            `${calls.toLocaleString()} AI calls included`,
                                            "24/7 AI Receptionist",
                                            "Real-time Appointment Booking",
                                            "Conversation Transcripts",
                                            "WhatsApp & SMS Integration"
                                        ].map((feat, i) => (
                                            <div key={i} className="flex items-start gap-3">
                                                <div className="bg-[#2C7A44] text-white rounded-full p-0.5 mt-0.5">
                                                    <Check size={12} strokeWidth={4} />
                                                </div>
                                                <span className="text-white/80 font-medium text-sm">{feat}</span>
                                            </div>
                                        ))}
                                    </div>

                                    <a
                                        href="/contact"
                                        className="w-full mt-auto py-4 rounded-xl bg-[#2C7A44] text-white font-bold text-center shadow-[0_0_20px_rgba(44,122,68,0.3)] hover:shadow-[0_0_30px_rgba(44,122,68,0.5)] hover:-translate-y-1 transition-all flex justify-center items-center gap-2 group"
                                    >
                                        {isEnterprise ? "Talk to Sales" : "Get Started"}
                                        <ArrowRight size={18} className="-rotate-45 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                                    </a>
                                </div>
                            </motion.div>
                        </div>
                    </div>

                    {/* Profit Analysis Panel (Owner Only) */}
                    <AdminView>
                        <div className="mt-12 pt-8 border-t border-white/5">
                            <button
                                onClick={() => setShowAnalysis(!showAnalysis)}
                                className="flex items-center gap-2 text-xs uppercase tracking-widest font-bold text-white/40 hover:text-white transition-colors mx-auto group bg-black/20 px-4 py-2 rounded-full hover:bg-black/40"
                            >
                                <Settings2 size={14} className="group-hover:rotate-45 transition-transform" />
                                {showAnalysis ? "Hide Profit Logic" : "Configure Profit Logic"}
                                {showAnalysis ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            </button>

                            <AnimatePresence>
                                {showAnalysis && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="overflow-hidden"
                                    >
                                        <div className="mt-6 bg-black/20 rounded-2xl p-6 border border-white/5 backdrop-blur-sm">
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

                                                {/* Inputs */}
                                                <div className="space-y-5">
                                                    <h4 className="text-sm font-bold text-white/80 flex items-center gap-2">
                                                        <Settings2 size={16} /> Cost Parameters
                                                    </h4>
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div className="space-y-1.5">
                                                            <label className="text-[10px] text-white/40 uppercase font-mono tracking-wider">Var. Cost ($/min)</label>
                                                            <input
                                                                type="number"
                                                                step="0.001"
                                                                value={costPerMinute}
                                                                onChange={(e) => setCostPerMinute(Number(e.target.value))}
                                                                className="w-full bg-[#0e2e22] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-[#2C7A44]/50 focus:ring-1 focus:ring-[#2C7A44]/50 outline-none transition-all"
                                                            />
                                                        </div>
                                                        <div className="space-y-1.5">
                                                            <label className="text-[10px] text-white/40 uppercase font-mono tracking-wider">Fixed ($/call)</label>
                                                            <input
                                                                type="number"
                                                                step="0.01"
                                                                value={costPerCallFixed}
                                                                onChange={(e) => setCostPerCallFixed(Number(e.target.value))}
                                                                className="w-full bg-[#0e2e22] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-[#2C7A44]/50 focus:ring-1 focus:ring-[#2C7A44]/50 outline-none transition-all"
                                                            />
                                                        </div>
                                                        <div className="space-y-1.5">
                                                            <label className="text-[10px] text-white/40 uppercase font-mono tracking-wider">Infra Cost ($/mo)</label>
                                                            <input
                                                                type="number"
                                                                step="1"
                                                                value={fixedInfraCost}
                                                                onChange={(e) => setFixedInfraCost(Number(e.target.value))}
                                                                className="w-full bg-[#0e2e22] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-[#2C7A44]/50 focus:ring-1 focus:ring-[#2C7A44]/50 outline-none transition-all"
                                                            />
                                                        </div>
                                                        <div className="space-y-1.5">
                                                            <div className="flex justify-between">
                                                                <label className="text-[10px] text-[#2C7A44] uppercase font-mono tracking-wider">Target Margin</label>
                                                                <span className="text-[10px] text-[#2C7A44] font-bold">{targetMargin}%</span>
                                                            </div>
                                                            <input
                                                                type="range"
                                                                min="10"
                                                                max="90"
                                                                step="1"
                                                                value={targetMargin}
                                                                onChange={(e) => setTargetMargin(Number(e.target.value))}
                                                                className="w-full accent-[#2C7A44] h-2 bg-[#0e2e22] rounded-full appearance-none cursor-pointer"
                                                            />
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Breakdown Visualization */}
                                                <div className="space-y-5">
                                                    <h4 className="text-sm font-bold text-white/80 flex items-center gap-2">
                                                        <Info size={16} /> Financial Breakdown
                                                    </h4>

                                                    {/* Bar Chart */}
                                                    <div className="space-y-2">
                                                        <div className="h-8 w-full bg-[#0e2e22] rounded-md overflow-hidden flex text-[10px] font-bold text-white">
                                                            <motion.div
                                                                initial={{ width: 0 }}
                                                                animate={{ width: `${100 - financials.margin}%` }}
                                                                className="h-full bg-red-400 flex items-center justify-center relative group cursor-help text-forest"
                                                            >
                                                                <span className="opacity-0 group-hover:opacity-100 transition-opacity">COST</span>
                                                            </motion.div>
                                                            <motion.div
                                                                initial={{ width: 0 }}
                                                                animate={{ width: `${financials.margin}%` }}
                                                                className="h-full bg-[#2C7A44] flex items-center justify-center relative group cursor-help"
                                                            >
                                                                <span className="opacity-0 group-hover:opacity-100 transition-opacity">PROFIT</span>
                                                            </motion.div>
                                                        </div>
                                                        <div className="flex justify-between text-[10px] text-white/40 font-mono">
                                                            <div className="flex items-center gap-1.5">
                                                                <div className="w-2 h-2 rounded-full bg-red-400"></div>
                                                                Total Cost: ${financials.totalCost.toFixed(2)}
                                                            </div>
                                                            <div className="flex items-center gap-1.5">
                                                                <div className="w-2 h-2 rounded-full bg-[#2C7A44]"></div>
                                                                Net Profit: ${financials.profit.toFixed(2)}
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <p className="text-white/30 text-xs leading-relaxed">
                                                        Pricing is dynamically calculated to achieve a <strong className="text-white/60">{targetMargin}% margin</strong>.
                                                        If costs rise (usage increases), the price adjusts automatically to maintain profitability.
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </AdminView>
                </div>
            </div>
        </section>
    );
};

export default Pricing;