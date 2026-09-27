import { LucideIcon, ArrowUpRight } from "lucide-react";

interface StatCardProps {
    title: string;
    value: string;
    icon?: LucideIcon;
    trend?: {
        value: string;
        isPositive: boolean;
    };
    variant?: "primary" | "highlight" | "success" | "warning" | "info";
    status?: string;
    badgeText?: string;
}

export const StatCard = ({ title, value, icon: Icon, trend, variant = "primary", badgeText }: StatCardProps) => {
    const isHighlight = variant === "highlight";

    return (
        <div
            className={`p-4 md:p-6 rounded-[20px] md:rounded-[24px] relative flex flex-col justify-between h-full min-h-[140px] md:min-h-[180px] overflow-hidden ${isHighlight
                    ? 'bg-gradient-to-br from-[#187848] via-[#0a4c2f] to-[#052b19] border border-[#1b8550]/20 text-white shadow-xl shadow-[#0a4c2f]/30'
                    : 'bg-white text-gray-900 shadow-[0_2px_15px_-4px_rgba(0,0,0,0.03)] border border-gray-100'
                }`}
        >
            {isHighlight && (
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-white/10 via-transparent to-transparent pointer-events-none"></div>
            )}
            <div className="flex justify-between items-start mb-2 md:mb-4 relative z-10 gap-2">
                <h3 className={`font-semibold text-[13px] md:text-base leading-tight ${isHighlight ? 'text-white/95' : 'text-gray-900'}`}>{title}</h3>
                <div className={`w-7 h-7 md:w-8 md:h-8 rounded-full flex items-center justify-center border shrink-0 ${isHighlight ? 'border-white bg-white text-[#0a4c2f]' : 'border-gray-300 text-gray-900 bg-white'
                    }`}>
                    <ArrowUpRight className="w-3 h-3 md:w-4 md:h-4 stroke-[2.5px]" />
                </div>
            </div>

            <div className="flex flex-col gap-1 md:gap-2 mt-auto">
                <div className={`text-[28px] md:text-[42px] font-bold leading-none tracking-tight ${isHighlight ? 'text-white' : 'text-gray-900'}`}>{value}</div>
                <div className="flex flex-wrap items-center gap-1 md:gap-2 mt-1 md:mt-0">
                    {badgeText && (
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold flex items-center justify-center min-w-[24px] ${isHighlight ? 'bg-white text-[#0a4c2f]' : 'bg-transparent text-gray-500 border border-gray-300'
                            }`}>
                            {badgeText}
                        </span>
                    )}
                    {trend && (
                        <span className={`text-[10px] md:text-[11px] font-semibold leading-none md:leading-normal ${isHighlight ? 'text-[#8abfa7]' : 'text-gray-500'}`}>
                            {trend.value}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
};
