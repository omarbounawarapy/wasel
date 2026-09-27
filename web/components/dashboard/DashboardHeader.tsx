"use client";

import { useEffect, useState } from "react";
import { Mail, Bell } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from "@/contexts/AuthContext";

export const DashboardHeader = () => {
    const { user } = useAuth();
    const displayName = user?.full_name?.trim() || user?.username?.trim() || "User";
    const displayEmail = user?.email || "";
    
    const initials = displayName
        .split(" ")
        .map((part) => part[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();

    return (
        <header className="h-auto md:h-[88px] py-2 md:py-0 px-2 md:px-8 flex flex-col md:flex-row items-center justify-end shrink-0 gap-4 md:gap-0 bg-[#f3f5f4]">
            <div className="flex items-center justify-between w-full md:w-auto gap-2 md:gap-5">
                {/* Action buttons */}
                <div className="flex items-center gap-2 md:gap-3">
                    <button className="w-10 h-10 md:w-11 md:h-11 bg-white rounded-full flex items-center justify-center shadow-[0_2px_10px_-4px_rgba(0,0,0,0.05)] border border-gray-200/50 text-gray-600 hover:text-gray-900 transition-colors">
                        <Mail className="w-4 h-4 md:w-5 md:h-5 stroke-2" />
                    </button>
                    <button className="w-10 h-10 md:w-11 md:h-11 bg-white rounded-full flex items-center justify-center shadow-[0_2px_10px_-4px_rgba(0,0,0,0.05)] border border-gray-200/50 text-gray-600 hover:text-gray-900 transition-colors relative">
                        <Bell className="w-4 h-4 md:w-5 md:h-5 stroke-2" />
                        <span className="absolute top-2.5 md:top-3 right-2.5 md:right-3 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
                    </button>
                </div>

                {/* User avatar pill */}
                <div className="flex items-center gap-2 md:gap-3 bg-white pl-2 pr-3 md:pl-2.5 md:pr-5 py-2 md:py-2.5 rounded-full shadow-[0_2px_10px_-4px_rgba(0,0,0,0.05)] border border-gray-200/50 cursor-pointer hover:bg-gray-50 transition-colors md:ml-2 shrink-0 max-w-[200px] md:max-w-none">
                    <Avatar className="w-8 h-8 md:w-9 md:h-9">
                        <AvatarFallback className="bg-gradient-to-br from-[#187848] to-[#0a4c2f] text-white text-sm font-bold">
                            {initials}
                        </AvatarFallback>
                    </Avatar>
                    <div className="flex flex-col min-w-0">
                        <span className="text-[13px] md:text-sm font-bold text-gray-900 leading-none mb-1 truncate">{displayName}</span>
                        <span className="text-[10px] md:text-[11px] font-medium text-gray-500 leading-none truncate">{displayEmail}</span>
                    </div>
                </div>
            </div>
        </header>
    );
};
