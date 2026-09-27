"use client";
import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Phone } from 'lucide-react';

const LogoMarquee = () => {
  const logos = [
    {
      name: "Wise",
      path: <path d="M 12.5 0 C 6.151 0 1 5.151 1 11.5 C 1 17.851 6.151 23 12.5 23 C 18.85 23 24 17.851 24 11.5 C 24 5.151 18.851 0 12.5 0 Z M 11.902 20.719 L 11.902 13.505 L 7.89 13.505 L 13.653 2.281 L 13.653 9.495 L 17.514 9.495 Z" fill="#2C7A44" />
    },
    {
      name: "Paypal",
      path: <><path d="M 11.214 0.006 C 11.163 0.011 10.998 0.028 10.85 0.039 C 7.442 0.347 4.249 2.186 2.226 5.012 C 1.1 6.584 0.38 8.367 0.108 10.255 C 0.012 10.914 0 11.109 0 12.002 C 0 12.896 0.012 13.091 0.108 13.75 C 0.76 18.256 3.967 22.042 8.317 23.445 C 9.096 23.696 9.917 23.867 10.85 23.97 C 11.214 24.01 12.786 24.01 13.15 23.97 C 14.761 23.792 16.127 23.393 17.473 22.706 C 17.68 22.6 17.72 22.572 17.691 22.549 C 17.673 22.535 16.793 21.355 15.737 19.928 L 13.818 17.336 L 11.413 13.778 C 10.09 11.822 9.002 10.222 8.992 10.222 C 8.983 10.22 8.974 11.801 8.969 13.731 C 8.962 17.111 8.96 17.247 8.917 17.327 C 8.856 17.442 8.809 17.489 8.711 17.541 C 8.636 17.578 8.57 17.585 8.216 17.585 L 7.81 17.585 L 7.702 17.517 C 7.635 17.475 7.581 17.416 7.545 17.346 L 7.496 17.24 L 7.5 12.537 L 7.507 7.832 L 7.58 7.74 C 7.618 7.691 7.697 7.628 7.754 7.597 C 7.85 7.55 7.887 7.546 8.293 7.546 C 8.772 7.546 8.852 7.564 8.976 7.7 C 9.011 7.738 10.313 9.699 11.871 12.061 C 13.429 14.423 15.559 17.648 16.605 19.232 L 18.506 22.11 L 18.602 22.047 C 19.453 21.493 20.354 20.705 21.067 19.884 C 22.585 18.141 23.564 16.016 23.892 13.75 C 23.988 13.091 24 12.896 24 12.002 C 24 11.109 23.988 10.914 23.892 10.255 C 23.24 5.749 20.033 1.963 15.683 0.56 C 14.916 0.311 14.1 0.14 13.185 0.037 C 12.96 0.013 11.409 -0.012 11.214 0.006 Z M 16.127 7.264 C 16.239 7.32 16.331 7.428 16.364 7.541 C 16.382 7.602 16.387 8.906 16.382 11.845 L 16.375 16.063 L 15.632 14.923 L 14.886 13.783 L 14.886 10.717 C 14.886 8.735 14.895 7.621 14.909 7.567 C 14.947 7.435 15.029 7.332 15.141 7.271 C 15.238 7.222 15.273 7.217 15.641 7.217 C 15.988 7.217 16.049 7.222 16.127 7.264 Z" fill="#2C7A44" /><path d="M 11.912 23.965 C 17.999 23.965 17.614 21.309 17.614 21.309 L 17.614 18.566 L 11.826 18.566 L 11.826 17.703 L 19.945 17.703 C 19.945 17.703 23.842 18.141 23.842 11.963 C 23.842 5.784 20.402 6.001 20.402 6.001 L 18.389 6.001 L 18.389 8.862 C 18.389 8.862 18.501 12.323 15.045 12.323 L 9.245 12.323 C 9.245 12.323 6.009 12.274 6.009 15.476 L 6.009 20.765 C 6.009 20.765 5.518 23.967 11.875 23.967 L 11.909 23.967 Z M 15.112 22.113 C 14.691 22.124 14.305 21.879 14.134 21.492 C 13.963 21.105 14.041 20.652 14.331 20.345 C 14.621 20.038 15.066 19.937 15.459 20.09 C 15.852 20.242 16.115 20.617 16.126 21.04 L 16.126 21.066 C 16.126 21.645 15.66 22.113 15.085 22.113 L 15.111 22.113 Z" fill="#2C7A44" /></>
    },
    {
      name: "Slack",
      path: <path d="M 2 16.5 C 2 8.492 8.492 2 16.5 2 C 24.508 2 31 8.492 31 16.5 C 31 24.508 24.508 31 16.5 31 C 8.492 31 2 24.508 2 16.5 Z M 20.372 14.728 C 19.456 10.686 17.292 9.357 17.058 8.849 C 16.804 8.491 16.545 7.854 16.545 7.854 C 16.541 7.843 16.534 7.824 16.526 7.806 C 16.5 8.164 16.486 8.302 16.148 8.663 C 15.623 9.074 12.932 11.332 12.713 15.924 C 12.509 20.207 15.807 22.759 16.253 23.085 L 16.304 23.121 L 16.304 23.118 C 16.307 23.139 16.446 24.137 16.543 25.195 L 16.893 25.195 C 16.975 24.447 17.097 23.705 17.261 22.971 L 17.289 22.952 C 17.489 22.809 17.679 22.654 17.859 22.486 L 17.879 22.468 C 18.827 21.592 20.532 19.566 20.515 16.336 C 20.511 15.797 20.464 15.259 20.372 14.728 Z M 16.506 20.666 C 16.506 20.666 16.506 14.659 16.704 14.66 C 16.859 14.66 17.059 22.409 17.059 22.409 C 16.784 22.376 16.506 21.134 16.506 20.666 Z" fill="#2C7A44" />
    },
    {
      name: "Lemonsqueezy",
      path: <g transform="translate(1 3)"><path d="M 17.678 12.978 C 17.678 11.543 16.478 10.38 14.999 10.38 C 13.519 10.38 12.32 11.543 12.32 12.978 C 12.32 14.412 13.52 15.575 14.999 15.575 C 16.479 15.575 17.678 14.412 17.678 12.978 Z" fill="#2C7A44" /><path d="M 30 12.976 C 30 15.752 26.007 17.221 23.765 17.862 C 24.344 20.118 24.996 24.196 22.492 25.602 C 19.997 27.002 16.781 24.386 15.055 22.772 C 13.325 24.394 9.997 26.993 7.483 25.588 C 4.986 24.191 5.717 20.184 6.297 17.929 C 3.984 17.289 0 15.787 0 12.976 C 0 10.156 3.988 8.776 6.315 8.136 C 5.737 5.893 4.968 1.828 7.462 0.428 C 9.966 -0.977 13.304 1.684 15.014 3.273 C 16.728 1.668 19.975 -1.005 22.47 0.39 C 24.977 1.791 24.266 5.924 23.7 8.154 C 25.99 8.792 30 10.183 30 12.976 Z M 28.718 12.976 C 28.718 10.901 25.036 9.823 23.357 9.351 C 22.954 10.593 22.466 11.806 21.897 12.982 C 22.488 14.174 22.996 15.405 23.416 16.667 C 25.185 16.159 28.718 15.07 28.718 12.976 Z M 22.526 18.178 C 21.186 18.47 19.829 18.673 18.462 18.785 C 17.695 19.873 16.855 20.907 15.948 21.881 C 17.222 23.07 19.988 25.571 21.85 24.526 C 23.72 23.476 22.933 19.773 22.526 18.178 Z M 14.158 21.886 C 13.233 20.915 12.372 19.885 11.582 18.801 C 10.224 18.7 8.873 18.511 7.54 18.233 C 7.113 19.895 6.261 23.47 8.124 24.511 C 9.995 25.557 13.075 22.901 14.158 21.886 Z M 6.64 16.732 C 7.049 15.458 7.543 14.213 8.12 13.006 C 7.55 11.816 7.062 10.589 6.658 9.333 C 4.941 9.803 1.28 10.874 1.28 12.976 C 1.28 15.079 5.003 16.278 6.64 16.732 Z M 7.557 7.83 C 8.799 7.556 10.15 7.353 11.56 7.226 C 12.343 6.148 13.197 5.124 14.116 4.16 C 12.874 3.01 9.974 0.454 8.104 1.504 C 6.236 2.552 7.091 6.02 7.557 7.83 Z M 21.155 11.545 C 21.517 10.727 21.838 9.891 22.115 9.041 C 21.254 8.85 20.336 8.694 19.379 8.577 C 20.012 9.541 20.605 10.531 21.155 11.545 Z M 13.234 7.114 C 14.415 7.06 15.599 7.06 16.78 7.114 C 16.226 6.396 15.637 5.707 15.014 5.048 C 14.387 5.707 13.793 6.396 13.234 7.114 Z M 8.857 11.545 C 9.398 10.527 9.988 9.536 10.623 8.575 C 9.71 8.684 8.802 8.834 7.903 9.027 C 8.179 9.881 8.497 10.721 8.857 11.544 Z M 8.858 14.467 C 8.476 15.343 8.15 16.205 7.886 17.035 C 8.8 17.224 9.722 17.368 10.65 17.466 C 10.005 16.496 9.407 15.495 8.858 14.467 Z M 16.811 18.891 C 15.623 18.942 14.433 18.942 13.245 18.897 C 13.812 19.624 14.414 20.323 15.05 20.991 C 15.673 20.322 16.26 19.621 16.811 18.891 Z M 21.166 14.423 C 20.613 15.455 20.015 16.462 19.376 17.443 C 20.316 17.336 21.25 17.182 22.174 16.981 C 21.906 16.166 21.567 15.308 21.167 14.422 Z M 20.476 12.988 C 19.668 11.403 18.753 9.876 17.737 8.416 C 15.916 8.282 14.089 8.282 12.268 8.416 C 11.242 9.874 10.329 11.408 9.538 13.006 C 10.334 14.607 11.252 16.144 12.284 17.604 C 14.103 17.721 15.928 17.717 17.747 17.594 C 18.761 16.123 19.673 14.584 20.476 12.988 Z M 15.912 4.159 C 16.826 5.124 17.673 6.149 18.448 7.228 C 19.797 7.347 21.137 7.552 22.46 7.843 C 22.868 6.227 23.7 2.513 21.83 1.467 C 19.978 0.431 17.17 2.984 15.912 4.159 Z" fill="#2C7A44" /></g>
    },
    {
      name: "Google",
      path: <g transform="translate(7 6)"><path d="M 0 0 L 25 0 L 25 24 L 0 24 Z" fill="#2C7A44" /><path d="M 11.207 8.936 L 11.547 8.947 L 11.806 8.961 L 11.806 9.094 L 10.694 9.094 L 10.59 9.344 C 10.388 9.674 10.225 9.754 9.861 9.894 C 10.172 9.229 10.414 8.903 11.207 8.936 Z M 16.293 8.893 C 16.902 9.013 17.205 9.406 17.533 9.879 L 17.533 10.412 L 17.811 10.412 C 18.092 10.906 18.369 11.4 18.645 11.896 L 18.885 12.319 L 19.113 12.73 L 19.325 13.107 C 19.498 13.529 19.52 13.829 19.478 14.279 C 19.287 14.596 19.287 14.596 19.061 14.812 L 18.783 14.812 L 18.783 15.079 C 18.005 15.096 17.227 15.108 16.448 15.116 C 16.183 15.119 15.919 15.124 15.654 15.129 C 15.273 15.138 14.892 15.141 14.511 15.144 L 14.154 15.155 C 13.573 15.155 13.296 15.122 12.801 14.808 C 12.463 14.308 12.422 13.918 12.533 13.346 C 12.727 12.878 12.727 12.878 12.995 12.415 L 13.14 12.163 C 13.24 11.989 13.342 11.815 13.445 11.643 C 13.6 11.379 13.754 11.114 13.905 10.848 C 15.077 8.834 15.077 8.834 16.293 8.893 Z M 7.109 8.873 C 7.769 9.041 8.197 9.486 8.551 10.027 C 8.922 10.713 8.922 10.713 8.922 11.079 L 9.2 11.079 L 9.296 10.812 C 9.599 10.147 9.988 9.407 10.589 8.946 C 11.015 8.854 11.41 8.87 11.839 8.946 C 12.264 9.221 12.264 9.221 12.533 9.612 C 12.71 10.591 12.165 11.309 11.674 12.138 L 11.431 12.56 C 11.2 12.957 10.966 13.353 10.728 13.746 L 10.533 14.074 L 10.356 14.363 L 10.206 14.61 C 9.87 15.004 9.515 15.075 9.001 15.138 C 8.362 15.062 8.228 14.872 7.811 14.412 C 7.543 13.998 7.543 13.998 7.293 13.54 L 7.157 13.294 C 7.015 13.037 6.875 12.779 6.735 12.521 C 6.639 12.346 6.543 12.172 6.447 11.997 C 5.506 10.287 5.506 10.287 5.589 9.612 C 6.001 9.044 6.37 8.824 7.109 8.873 Z" fill="#2C7A44" /></g>
    }
  ];

  // Create a duplicated array for infinite scroll illusion, enough to cover width
  const marqueeLogos = [...logos, ...logos, ...logos, ...logos, ...logos];

  return (
    <div className="w-full flex flex-col gap-3 relative mt-auto opacity-90">

      <div className="w-full overflow-hidden" style={{ maskImage: 'linear-gradient(to right, transparent, black 10%, black 90%, transparent)', WebkitMaskImage: 'linear-gradient(to right, transparent, black 10%, black 90%, transparent)' }}>
        {/* Row 1 - Left */}
        <motion.div
          className="flex gap-3 w-max mb-3"
          animate={{ x: "-50%" }}
          initial={{ x: "0%" }}
          transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
        >
          {marqueeLogos.map((logo, i) => (
            <div key={`r1-${i}`} className="w-14 h-14 bg-[#142e22] rounded-xl flex items-center justify-center border border-white/5 shrink-0 shadow-lg group">
              <svg viewBox="0 0 24 24" className="w-7 h-7 fill-[#2C7A44] opacity-80 group-hover:opacity-100 transition-opacity">
                {logo.path}
              </svg>
            </div>
          ))}
        </motion.div>

        {/* Row 2 - Right (Inverse) */}
        <motion.div
          className="flex gap-3 w-max"
          animate={{ x: "0%" }}
          initial={{ x: "-50%" }}
          transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
        >
          {marqueeLogos.map((logo, i) => (
            <div key={`r2-${i}`} className="w-14 h-14 bg-[#142e22] rounded-xl flex items-center justify-center border border-white/5 shrink-0 shadow-lg group">
              <svg viewBox="0 0 24 24" className="w-7 h-7 fill-[#2C7A44] opacity-80 group-hover:opacity-100 transition-opacity">
                {logo.path}
              </svg>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
};

const BentoGrid: React.FC = () => {
  return (
    <section id="features" className="py-24 px-5 bg-sage">
      <div className="max-w-[1000px] mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 mb-16">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="md:max-w-[500px]"
          >
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-manrope font-bold leading-tight">
              See your appointments in real time, clearly
            </h2>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="md:max-w-[320px]"
          >
            <p className="text-white/60 font-manrope text-lg leading-relaxed">
              Calleem shows your appointments, calls, and AI performance in simple visuals you can act on – right away.
            </p>
          </motion.div>
        </div>

        {/* Grid Container */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">

          {/* Card 1: Large Span */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="md:col-span-3 bg-forest rounded-[30px] p-2 flex flex-col gap-6 overflow-hidden group hover:shadow-2xl transition-shadow duration-500"
          >
            <div className="relative h-[250px] md:h-[450px] w-full rounded-[25px] overflow-hidden bg-black/20">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/hero-dashboard.png"
                alt="Dashboard"
                className="absolute inset-0 w-full h-full object-cover object-top opacity-90 group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-forest to-transparent opacity-80"></div>
            </div>
            <div className="px-6 pb-8">
              <h4 className="text-2xl font-bold font-manrope mb-2">AI Receptionist Dashboard</h4>
              <p className="text-white/60">See all your analytics in one view</p>
            </div>
          </motion.div>

          {/* Card 2: Medium Span */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="md:col-span-2 bg-forest rounded-[30px] p-2 flex flex-col gap-6 overflow-hidden group"
          >
            <div className="relative h-[250px] w-full rounded-[25px] overflow-hidden bg-black/20">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/appointments.png"
                alt="Appointments"
                className="absolute inset-0 w-full h-full object-cover object-top opacity-90 group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-forest to-transparent opacity-60"></div>
            </div>
            <div className="px-6 pb-8">
              <h4 className="text-2xl font-bold font-manrope mb-2">Appointment Overview</h4>
              <p className="text-white/60">Manage your schedule efficiently</p>
            </div>
          </motion.div>

          {/* Card 3: Small Span */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="md:col-span-1 bg-forest rounded-[30px] p-2 flex flex-col gap-6 overflow-hidden group"
          >
            <div className="relative h-[250px] w-full rounded-[25px] overflow-hidden bg-black/20">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/call-history.png"
                alt="Call History"
                className="absolute inset-0 w-full h-full object-cover object-top opacity-90 group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-forest to-transparent opacity-60"></div>
            </div>
            <div className="px-6 pb-8">
              <h4 className="text-2xl font-bold font-manrope mb-2">Call History</h4>
              <p className="text-white/60">Review past conversations</p>
            </div>
          </motion.div>

          {/* Card 4: Small Span (Testing Playground) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="hidden md:col-span-1 bg-forest rounded-[30px] p-2 flex flex-col gap-6 overflow-hidden group"
          >
            <div className="relative h-[250px] w-full rounded-[25px] overflow-hidden bg-[#0d1f16] flex items-center justify-center">
              {/* Animation Overlay */}
              <div className="relative z-10 flex flex-col items-center">
                <div className="relative">
                  {[1, 2, 3].map((i) => (
                    <motion.div
                      key={i}
                      className="absolute inset-0 border border-[#2C7A44]/30 rounded-full"
                      initial={{ scale: 1, opacity: 1 }}
                      animate={{ scale: 2.5, opacity: 0 }}
                      transition={{ duration: 2, repeat: Infinity, delay: i * 0.6, ease: "easeOut" }}
                    />
                  ))}
                  <div className="bg-[#2C7A44] text-white p-4 rounded-full shadow-[0_0_30px_rgba(44,122,68,0.4)] relative z-10">
                    <Phone size={24} className="fill-current" />
                  </div>
                </div>
                <motion.div
                  initial={{ opacity: 0.5 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 1, repeat: Infinity, repeatType: "reverse" }}
                  className="mt-6 px-3 py-1 bg-white/5 border border-white/10 rounded-full backdrop-blur-sm"
                >
                  <span className="text-xs font-mono text-[#2C7A44] tracking-widest uppercase">Listening...</span>
                </motion.div>
              </div>

              {/* Background Waveform Effect */}
              <div className="absolute bottom-0 left-0 right-0 h-1/2 flex items-end justify-center gap-1 opacity-20 pointer-events-none">
                {[...Array(12)].map((_, i) => (
                  <motion.div
                    key={i}
                    className="w-2 bg-[#2C7A44] rounded-t-sm"
                    animate={{ height: ["10%", "60%", "30%", "80%", "20%"] }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear", delay: i * 0.1 }}
                  />
                ))}
              </div>
            </div>
            <div className="px-6 pb-8">
              <h4 className="text-2xl font-bold font-manrope mb-2">Testing Playground</h4>
              <p className="text-white/60">Test your AI assistant live</p>
            </div>
          </motion.div>

          {/* Card 5: Medium Span with Social Proof and CTA - Updated with Marquee */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="hidden md:col-span-2 bg-[#0e2e22] rounded-[30px] p-8 flex flex-col md:flex-row gap-8 items-start justify-between relative overflow-hidden"
          >
            {/* Social Proof Side */}
            <div className="flex flex-col justify-between z-10 w-full md:w-1/2 h-full gap-8">
              <div className="flex flex-col gap-4">
                <div className="flex -space-x-3">
                  {[
                    "https://framerusercontent.com/images/dA3S2peWT6oWoeewM4Bvyue9U.png?scale-down-to=512",
                    "https://framerusercontent.com/images/rMTwN2rk0lG5miPrJLisO8pbAw.png?scale-down-to=512",
                    "https://framerusercontent.com/images/0k67Xy4DBWDsp2JSVVypJyz8Q.png?scale-down-to=512"
                  ].map((src, i) => (
                    <React.Fragment key={i}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={src} className="w-12 h-12 rounded-full border-4 border-forest object-cover" alt="User" />
                    </React.Fragment>
                  ))}
                </div>
                <h4 className="text-xl font-bold font-manrope text-white">Trusted by many Businesses</h4>
              </div>

              {/* Infinite Marquee */}
              <LogoMarquee />
            </div>

            {/* Stats Side */}
            <div className="flex flex-col gap-4 z-10 w-full md:w-1/2 md:pl-8 md:border-l border-white/5 h-full justify-start">
              <div>
                <h3 className="text-3xl md:text-4xl font-extrabold font-inter mb-2 text-white">14 Hours Saved</h3>
                <p className="text-white/60 text-sm leading-relaxed">
                  Calleem helps businesses save time – and serve customers smarter.
                </p>
              </div>
              <div className="pt-4 mt-auto">
                <a href="/contact" className="inline-flex items-center gap-2 text-white hover:text-white/80 font-bold transition-colors group">
                  Request Access <ArrowRight size={18} className="-rotate-45 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                </a>
              </div>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
};

export default BentoGrid;