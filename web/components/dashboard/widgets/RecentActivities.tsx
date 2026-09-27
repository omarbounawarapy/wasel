import { Phone, Clock } from "lucide-react";

export const RecentActivities = () => {
    return (
        <div className="bg-white rounded-[24px] shadow-[0_2px_15px_-4px_rgba(0,0,0,0.03)] border border-gray-100 p-6">
            <h3 className="font-bold text-lg text-gray-900 mb-4">Recent Activity</h3>

            <div className="rounded-xl p-4 mb-4 bg-gray-50 border border-gray-100">
                <div className="flex items-start justify-between mb-3">
                    <div>
                        <h4 className="font-bold text-gray-900 mb-1">Priority Support Call</h4>
                        <p className="text-sm text-gray-500">Enterprise client escalation</p>
                    </div>
                    <Phone className="w-5 h-5 text-[#0a4c2f]" />
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                    <Clock className="w-4 h-4" />
                    <span>Starting in 15 minutes</span>
                </div>
                <button className="w-full px-4 py-2.5 bg-gradient-to-b from-[#187848] via-[#0a4c2f] to-[#052b19] text-white rounded-xl font-semibold transition-all shadow-[0_4px_16px_rgba(10,76,47,0.3)] relative overflow-hidden">
                    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white/20 via-transparent to-transparent opacity-50"></div>
                    <span className="relative z-10">Join Call</span>
                </button>
            </div>

            <div className="space-y-3">
                {[
                    { color: "bg-green-500", text: "Ticket #2847 resolved", time: "2m ago" },
                    { color: "bg-amber-500", text: "New escalation assigned", time: "5m ago" },
                    { color: "bg-[#0a4c2f]", text: "Call with Tech Corp ended", time: "12m ago" },
                ].map((item, i) => (
                    <div key={i} className="flex items-center gap-3 text-sm">
                        <div className={`w-2 h-2 rounded-full ${item.color}`} />
                        <span className="text-gray-500">{item.text}</span>
                        <span className="ml-auto text-xs text-gray-400">{item.time}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};
