"use client";

import {
    LayoutDashboard,
    Users,
    BarChart3,
    Settings,
    Shield,
    Database,
    Activity,
    Calendar,
    MessageSquare,
    Scissors,
    Building2,
    Mail,
    LogOut,
    Clock,
    CreditCard,
} from "lucide-react";
import { NavLink } from "../dashboard/NavLink";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

const menuItems = [
    // 1. Business Data
    {
        label: "Business Data",
        items: [
            { icon: Building2, label: "Tenants", path: "/admin/tenants" },
            { icon: Users, label: "Users (Business Owners)", path: "/admin/users" },
            { icon: Clock, label: "Pending Users", path: "/admin/users?filter=pending" },
            { icon: Calendar, label: "Appointments", path: "/admin/appointments" },
            { icon: Scissors, label: "Services", path: "/admin/services" },
            { icon: MessageSquare, label: "Conversations", path: "/admin/conversations" },
            { icon: Mail, label: "Contact Submissions", path: "/admin/contacts" },
        ]
    },
    // 2. Analytics & Monitoring
    {
        label: "Analytics & Monitoring",
        items: [
            { icon: BarChart3, label: "Analytics", path: "/admin/analytics" },
            { icon: Activity, label: "System Health", path: "/admin/system" },
            { icon: CreditCard, label: "Billing", path: "/admin/billing" },
        ]
    },
    // 3. System Control
    {
        label: "System Control",
        items: [
            { icon: Database, label: "Database Config", path: "/admin/config" },
            { icon: Settings, label: "Global Settings", path: "/admin/settings" },
        ]
    }
];

export const AdminSidebar = () => {
    const pathname = usePathname();
    const { logout } = useAuth();

    return (
        <aside className="fixed left-0 top-0 h-screen w-64 glass-strong flex flex-col z-50 overflow-y-auto border-r border-white/20 bg-slate-900 text-white">
            <div className="p-6">
                <div className="flex items-center gap-2">
                    <div className="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center shadow-lg shadow-red-500/30">
                        <Shield className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-xl font-bold text-white truncate">
                        Admin Panel
                    </span>
                </div>
            </div>

            <nav className="flex-1 px-3">
                <div className="mb-6 space-y-6">
                    <NavLink
                        href="/admin"
                        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all hover:bg-white/50 hover:text-primary hover:shadow-md mx-3"
                        activeClassName="bg-primary text-white shadow-lg shadow-primary/30"
                    >
                        <LayoutDashboard className="w-5 h-5" />
                        <span>Dashboard</span>
                    </NavLink>

                    {menuItems.map((section, idx) => (
                        <div key={idx}>
                            <p className="px-6 text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                                {section.label}
                            </p>
                            <div className="space-y-1 px-3">
                                {section.items.map((item) => (
                                    <NavLink
                                        key={item.path}
                                        href={item.path}
                                        className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all hover:bg-white/50 hover:text-primary hover:shadow-md"
                                        activeClassName="bg-primary/80 text-white shadow-lg shadow-primary/20"
                                    >
                                        <item.icon className="w-4 h-4" />
                                        <span>{item.label}</span>
                                    </NavLink>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </nav>

            <div className="p-4 m-4 bg-slate-800 rounded-2xl text-slate-300 text-xs border border-slate-700">
                <p className="font-semibold mb-1">System Status</p>
                <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    <span>All Systems Online</span>
                </div>

                <button
                    onClick={logout}
                    className="flex items-center gap-2 w-full px-3 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors mt-2"
                >
                    <LogOut className="w-3 h-3" />
                    <span>Sign Out</span>
                </button>
            </div>
        </aside>
    );
};
