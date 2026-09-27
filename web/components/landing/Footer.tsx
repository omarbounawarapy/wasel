"use client";
import React from 'react';
import Link from 'next/link';

const Footer: React.FC = () => {
    return (
        <footer className="bg-sage text-white py-12 px-5 border-t border-white/5">
            <div className="max-w-[1200px] mx-auto flex flex-col md:flex-row justify-between gap-12">

                {/* Brand Area */}
                <div className="flex flex-col justify-between items-start gap-8 md:w-1/3">
                    <div className="flex flex-col gap-6">
                        <Link href="/" className="flex items-center gap-2 group">
                            <svg
                                className="w-8 h-6 text-white"
                                viewBox="0 0 41 24"
                                fill="currentColor"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <g transform="translate(0 0.5)">
                                    <path d="M 21.821 0.929 C 22.354 0.38 23.092 0.068 23.865 0.065 L 33.762 0.065 C 40.198 0.065 43.42 8.011 38.869 12.659 L 28.958 22.783 C 28.503 23.247 27.725 22.918 27.725 22.26 L 27.725 13.345 L 28.87 12.174 C 29.78 11.245 29.136 9.656 27.848 9.656 L 13.276 9.656 L 21.821 0.929 Z" fill="currentColor"></path>
                                    <path d="M 19.179 22.071 C 18.646 22.62 17.908 22.932 17.135 22.935 L 7.238 22.935 C 0.802 22.935 -2.42 14.988 2.131 10.341 L 12.042 0.217 C 12.497 -0.247 13.276 0.082 13.276 0.739 L 13.276 9.655 L 12.13 10.825 C 11.22 11.755 11.864 13.344 13.152 13.344 L 27.724 13.344 L 19.178 22.071 Z" fill="currentColor"></path>
                                </g>
                            </svg>
                            <span className="text-xl font-manrope font-semibold tracking-tight">Calleem</span>
                        </Link>
                        <p className="text-white/70 text-sm leading-relaxed max-w-xs">
                            Your 24/7 AI-powered receptionist.<br />
                            Never miss a call, automate booking, and manage appointments—effortlessly.
                        </p>
                    </div>
                    <div className="text-xs text-white/40 flex items-center gap-1">
                        Designed by <span className="text-[#1c3824] font-bold">Calleem</span> © 2025
                    </div>
                </div>

                {/* Links Area */}
                <div className="flex gap-20">
                    <div className="flex flex-col gap-6">
                        <h6 className="text-white font-bold font-manrope">Quick Menu</h6>
                        <div className="flex flex-col gap-4 text-white/70 text-sm">
                            <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
                            <a href="#features" className="hover:text-white transition-colors">Features</a>
                            <a href="#testimonials" className="hover:text-white transition-colors">Testimonials</a>
                            <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
                        </div>
                    </div>
                    <div className="flex flex-col gap-6">
                        <h6 className="text-white font-bold font-manrope">Information</h6>
                        <div className="flex flex-col gap-4 text-white/70 text-sm">
                            <a href="/contact" className="hover:text-white transition-colors">Contact Us</a>
                            <a href="/contact" className="hover:text-white transition-colors">Request Access</a>
                        </div>
                    </div>
                </div>

            </div>
        </footer>
    );
};

export default Footer;