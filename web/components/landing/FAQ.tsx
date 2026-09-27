"use client";

import React, { useState } from 'react';
import { FAQ_ITEMS } from './contact-constants';
import { Plus, Minus, ArrowUpRight } from 'lucide-react';

const FAQ: React.FC = () => {
  const [openId, setOpenId] = useState<string>('1');

  const toggleFAQ = (id: string) => {
    setOpenId(openId === id ? '' : id);
  };

  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": FAQ_ITEMS.map(item => ({
      "@type": "Question",
      "name": item.question,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": item.answer
      }
    }))
  };

  return (
    <section id="faq" className="w-full bg-[#648768] py-24 px-6 md:px-10 flex justify-center">
      <script
        type="application/ld-json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <div className="w-full max-w-[800px] flex flex-col items-center gap-12">

        {/* Headline */}
        <div className="flex flex-col items-center text-center gap-6">
          <h2 className="font-manrope font-bold text-[36px] md:text-[42px] leading-[1.2] text-white">
            Got questions? We’ve got answers.
          </h2>

          <div className="flex flex-col items-center gap-4">
            <p className="text-[16px] md:text-[18px] text-white/65 leading-[1.5]">
              Here’s everything you need to know before getting started.
            </p>
            <a href="#contact" className="group flex items-center gap-2 text-[#92b874] hover:text-white transition-colors text-[15px] font-semibold">
              Contact us
              <ArrowUpRight className="w-4 h-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
            </a>
          </div>
        </div>

        {/* Accordion */}
        <div className="flex flex-col gap-5 w-full">
          {FAQ_ITEMS.map((item) => {
            const isOpen = openId === item.id;
            return (
              <div
                key={item.id}
                onClick={() => toggleFAQ(item.id)}
                className={`w-full rounded-[20px] border-[3px] border-[#171717] bg-[#0e2e22] transition-all duration-300 cursor-pointer overflow-hidden ${isOpen ? 'pb-8' : ''}`}
              >
                <div className="p-6 md:px-8 md:py-6 flex items-center gap-6 md:gap-8">
                  {/* Number Badge */}
                  <div className="shrink-0 w-12 h-12 md:w-14 md:h-14 rounded-full bg-[#1d331a] flex items-center justify-center shadow-[0_1px_13px_0px_rgba(10,9,9,0.2)]">
                    <span className="font-manrope font-semibold text-white text-lg">{item.number}</span>
                  </div>

                  {/* Question Text */}
                  <div className="flex-1">
                    <h4 className="font-manrope font-bold text-[18px] md:text-[20px] leading-tight text-white">
                      {item.question}
                    </h4>
                  </div>

                  {/* Toggle Icon */}
                  <div className="shrink-0 text-white/50">
                    {isOpen ? <Minus className="w-6 h-6" /> : <Plus className="w-6 h-6" />}
                  </div>
                </div>

                {/* Answer Content */}
                <div
                  className={`px-6 md:px-8 md:pl-[104px] grid transition-[grid-template-rows] duration-300 ease-out ${isOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}
                >
                  <div className="overflow-hidden">
                    <p className="text-[15px] md:text-[16px] text-white/60 leading-[1.5]">
                      {item.answer}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
};

export default FAQ;