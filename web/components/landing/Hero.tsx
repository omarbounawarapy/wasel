"use client";
import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';

const Hero: React.FC = () => {
  return (
    <section className="relative pt-32 md:pt-48 pb-20 px-5 overflow-hidden">
      <div className="max-w-[1200px] mx-auto flex flex-col items-center gap-10 z-10 relative">

        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="bg-[#1d331a] border border-[#1c1c1c] rounded-full px-4 py-1.5 shadow-card"
        >
          <p className="text-sm font-medium text-[#fcfcfc] tracking-wide">All-in-One Dashboard</p>
        </motion.div>

        {/* Headline */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="max-w-[800px] text-center"
        >
          <h1 className="font-host font-bold text-4xl md:text-6xl lg:text-7xl leading-[1.1] md:leading-tight mb-6">
            Never Miss a Call Again With AI Receptionist 24/7
          </h1>
          <p className="text-lg md:text-xl text-white/60 font-manrope max-w-[600px] mx-auto leading-relaxed">
            Automate inbound calls, appointment booking, and customer conversations with AI-powered voice assistant — available 24/7
          </p>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <a
            href="/contact"
            className="bg-[#2C7A44] hover:bg-[#2C7A44]/90 text-white px-8 py-4 rounded-full text-base font-bold transition-all shadow-[0_0_20px_rgba(44,122,68,0.3)] hover:shadow-[0_0_30px_rgba(44,122,68,0.5)] flex items-center gap-3 group hover:-translate-y-1"
          >
            Request Access
            <ArrowRight size={20} className="-rotate-45 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
          </a>
        </motion.div>

        {/* Dashboard Visual */}
        <motion.div
          initial={{ opacity: 0, y: 100, rotateX: 10 }}
          animate={{ opacity: 1, y: 0, rotateX: 0 }}
          transition={{
            type: "spring",
            stiffness: 100,
            damping: 20,
            delay: 0.4
          }}
          className="w-full max-w-[1000px] mt-10 perspective-1000"
          style={{ perspective: '1000px' }}
        >
          <div className="relative w-full">
            {/* Glow Effect */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[60%] h-[100px] bg-[#fcfafa] opacity-20 blur-[80px] rounded-full z-0"></div>

            {/* Image Container */}
            <div className="relative z-10 w-full bg-dark rounded-[20px] md:rounded-[30px] p-1 md:p-2 border border-white/10 shadow-2xl backdrop-blur-sm overflow-hidden">
              <div className="relative w-full rounded-[12px] overflow-hidden bg-black">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/hero-dashboard.png"
                  alt="Calleem Dashboard"
                  className="w-full h-auto block"
                />
                {/* Green Line Gradient */}
                <div className="absolute top-0 left-[30%] w-[40%] h-[1px] bg-gradient-to-r from-transparent via-[#2C7A44] to-transparent z-20"></div>
              </div>
            </div>
          </div>
        </motion.div>

      </div>
    </section>
  );
};

export default Hero;