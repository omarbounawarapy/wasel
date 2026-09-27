"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Menu, X, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Navbar: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    setIsMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled ? 'py-4' : 'py-6'
        }`}
    >
      <div className="max-w-[1200px] mx-auto px-5 md:px-10">
        <div
          className={`flex items-center justify-between px-6 py-4 rounded-full transition-all duration-300 ${isScrolled
            ? 'bg-forest/80 backdrop-blur-md border border-white/10 shadow-lg'
            : 'bg-transparent'
            }`}
        >
          {/* Logo */}
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
            <span className="text-2xl font-host font-bold tracking-tight text-white">Calleem</span>
          </Link>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center gap-8">
            <button onClick={() => scrollToSection('how-it-works')} className="text-sm font-medium hover:text-white/80 transition-colors">How it works</button>
            <button onClick={() => scrollToSection('features')} className="text-sm font-medium hover:text-white/80 transition-colors">Features</button>
            <button onClick={() => scrollToSection('pricing')} className="text-sm font-medium hover:text-white/80 transition-colors">Pricing</button>
            <button onClick={() => scrollToSection('faq')} className="text-sm font-medium hover:text-white/80 transition-colors">FAQ</button>
            <a href="/contact" className="text-sm font-medium hover:text-white/80 transition-colors">Contact</a>
          </div>

          <div className="hidden md:block">
            <a
              href="/contact"
              className="bg-[#2C7A44] hover:bg-[#2C7A44]/90 text-white px-6 py-2.5 rounded-full text-sm font-bold transition-all shadow-[0_0_15px_rgba(44,122,68,0.3)] hover:shadow-[0_0_25px_rgba(44,122,68,0.5)] flex items-center gap-2 group"
            >
              Request Access
              <ArrowRight size={16} className="-rotate-45 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </a>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            className="md:hidden p-2 text-white bg-white/10 rounded-full hover:bg-white/20 transition-colors"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="absolute top-full left-0 w-full bg-forest/95 backdrop-blur-xl border-b border-white/10 shadow-2xl overflow-hidden"
          >
            <div className="p-6 flex flex-col gap-6">
              <button onClick={() => scrollToSection('how-it-works')} className="text-lg font-medium text-left text-white/90 hover:text-white transition-colors">How it works</button>
              <button onClick={() => scrollToSection('features')} className="text-lg font-medium text-left text-white/90 hover:text-white transition-colors">Features</button>
              <button onClick={() => scrollToSection('pricing')} className="text-lg font-medium text-left text-white/90 hover:text-white transition-colors">Pricing</button>
              <button onClick={() => scrollToSection('faq')} className="text-lg font-medium text-left text-white/90 hover:text-white transition-colors">FAQ</button>
              <a href="/contact" className="text-lg font-medium text-left text-white/90 hover:text-white transition-colors" onClick={() => setIsMobileMenuOpen(false)}>Contact</a>
              <a
                href="/contact"
                className="bg-[#2C7A44] text-center text-white px-5 py-3 rounded-xl text-lg font-bold shadow-[0_0_20px_rgba(44,122,68,0.2)] hover:bg-[#2C7A44]/90 transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Request Access
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navbar;