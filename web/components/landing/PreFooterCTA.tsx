import React from 'react';
import { ArrowRight } from 'lucide-react';

const CTA: React.FC = () => {
    return (
        <section className="py-24 px-5 bg-sage flex justify-center">
            <div className="w-full max-w-[1000px] bg-forest rounded-[30px] shadow-[0px_140px_120px_-80px_rgba(99,106,125,0.04)] overflow-hidden flex flex-col-reverse md:flex-row relative border border-white/5">

                {/* Text Content */}
                <div className="w-full md:w-1/2 p-10 md:p-14 flex flex-col justify-center items-start gap-6 z-10 relative bg-forest md:bg-transparent">
                    <h2 className="text-3xl md:text-5xl font-bold font-manrope leading-tight text-white">
                        Ready to automate your appointments with AI?
                    </h2>
                    <p className="text-white/60 text-lg leading-relaxed max-w-md">
                        Join the waitlist to be among the first to experience Calleem —and get early adopter pricing when we launch.
                    </p>
                    <div className="pt-2">
                        <a
                            href="#contact"
                            className="bg-[#2C7A44] hover:bg-[#2C7A44]/90 text-white px-8 py-4 rounded-full text-base font-bold transition-all shadow-[0_0_20px_rgba(44,122,68,0.3)] hover:shadow-[0_0_30px_rgba(44,122,68,0.5)] inline-flex items-center gap-3 group hover:-translate-y-1"
                        >
                            Request Access
                            <ArrowRight size={20} className="-rotate-45 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                        </a>
                    </div>
                </div>

                {/* Image */}
                <div className="w-full md:w-1/2 h-[500px] md:h-auto relative">
                    <div className="absolute inset-0">
                        <img
                            src="https://framerusercontent.com/images/AsfW6nRtd8870rS0nxiZalBmjno.webp?width=1368&height=1920"
                            alt="Happy woman using Calleem"
                            className="w-full h-full object-cover object-top"
                        />
                        {/* Gradient Overlay for Mobile (Bottom Fade) */}
                        <div className="absolute inset-0 bg-gradient-to-t from-forest via-forest/10 to-transparent md:hidden"></div>

                        {/* Gradient Overlay for Desktop (Left Fade) */}
                        <div className="absolute inset-0 hidden md:block bg-gradient-to-r from-forest via-forest/5 to-transparent"></div>
                    </div>
                </div>

            </div>
        </section>
    );
};

export default CTA;
