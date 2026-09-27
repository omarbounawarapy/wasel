import React from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { 
    User, 
    Phone, 
    Calendar, 
    Clock, 
    AlignLeft, 
    Timer, 
    Scissors, 
    Loader2 
} from "lucide-react";
import { useAppointmentForm } from "@/hooks/domain/useAppointmentForm";
import { AppointmentResponse } from "@/lib/types";
import PhoneInput from 'react-phone-number-input';
import 'react-phone-number-input/style.css';

interface AppointmentFormModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    appointment?: AppointmentResponse | null;
    mode: "create" | "edit";
    onSuccess?: () => void;
}

export default function AppointmentFormModal({
    open,
    onOpenChange,
    appointment,
    mode,
    onSuccess
}: AppointmentFormModalProps) {
    const { formData, setFormData, services, timeSlots, submit, isLoading } = useAppointmentForm({
        mode,
        appointment,
        onSuccess: () => {
            onSuccess?.();
            onOpenChange(false);
        }
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await submit();
    };

    // Custom Dropdown Arrow SVG for the select inputs
    const SelectArrow = () => (
        <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
        </div>
    );

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-xl p-0 rounded-[2.5rem] overflow-hidden border-0 shadow-2xl">
                {/* Premium Gradient Top Line */}
                <div className="absolute top-0 inset-x-0 h-2 bg-gradient-to-r from-[#064e3b] to-emerald-500" />
                
                <form onSubmit={handleSubmit} className="p-8">
                    <div className="mb-8">
                        <DialogHeader>
                            <DialogTitle className="text-2xl font-black text-slate-900 mb-1">
                                {mode === "create" ? "Book Appointment" : "Edit Appointment"}
                            </DialogTitle>
                            <DialogDescription className="text-slate-500 font-medium text-sm">
                                {mode === "create" ? "Schedule a new session for a client." : "Update the appointment details below."}
                            </DialogDescription>
                        </DialogHeader>
                    </div>

                    <div className="space-y-5">
                        {/* Client Name & Phone */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div className="space-y-1.5">
                                <label htmlFor="client_name" className="text-sm font-bold text-slate-700 ml-1">
                                    Client Name <span className="text-emerald-500">*</span>
                                </label>
                                <div className="relative">
                                    <div className="absolute left-0 pl-4 inset-y-0 flex items-center pointer-events-none">
                                        <User className="h-5 w-5 text-slate-400" />
                                    </div>
                                    <input
                                        id="client_name"
                                        type="text"
                                        value={formData.client_name}
                                        onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                                        placeholder="e.g., John Doe"
                                        required
                                        className="w-full pl-11 pr-4 py-3 bg-white/50 border border-slate-200/60 rounded-2xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-[#064e3b]/10 focus:border-[#064e3b] transition-all duration-300 shadow-sm"
                                    />
                                </div>
                            </div>
                            <div className="space-y-1.5">
                                <label htmlFor="client_phone" className="text-sm font-bold text-slate-700 ml-1">
                                    Phone Number <span className="text-emerald-500">*</span>
                                </label>
                                <div className="relative">
                                    <div className="absolute left-0 pl-4 inset-y-0 flex items-center pointer-events-none z-10">
                                        <Phone className="h-5 w-5 text-slate-400" />
                                    </div>
                                    <PhoneInput
                                        id="client_phone"
                                        international
                                        defaultCountry="US"
                                        value={formData.client_phone}
                                        onChange={(value) => setFormData({ ...formData, client_phone: value ? value.toString() : '' })}
                                        className="w-full pl-11 pr-4 py-3 bg-white/50 border border-slate-200/60 rounded-2xl text-slate-900 transition-all duration-300 shadow-sm focus-within:ring-4 focus-within:ring-[#064e3b]/10 focus-within:border-[#064e3b]"
                                        style={{
                                            '--PhoneInput-color--focus': 'transparent',
                                            '--PhoneInputCountryFlag-height': '20px',
                                            '--PhoneInputCountrySelectArrow-color': '#94a3b8',
                                            '--PhoneInputCountrySelectArrow-color--focus': '#064e3b',
                                        } as React.CSSProperties}
                                    />
                                    <style jsx global>{`
                                        .PhoneInputInput {
                                            border: none;
                                            background: transparent;
                                            outline: none;
                                            width: 100%;
                                            padding-left: 8px;
                                        }
                                        .PhoneInputCountry {
                                            margin-right: 8px;
                                            padding-right: 8px;
                                            border-right: 1px solid #e2e8f0;
                                        }
                                    `}</style>
                                </div>
                            </div>
                        </div>

                        {/* Service Selection Dropdown */}
                        <div className="space-y-1.5">
                            <label htmlFor="service" className="text-sm font-bold text-slate-700 ml-1">
                                Service <span className="text-emerald-500">*</span>
                            </label>
                            <div className="relative">
                                <div className="absolute left-0 pl-4 inset-y-0 flex items-center pointer-events-none">
                                    <Scissors className="h-5 w-5 text-slate-400" />
                                </div>
                                <select
                                    id="service"
                                    value={formData.service}
                                    onChange={(e) => setFormData({ ...formData, service: e.target.value })}
                                    required
                                    className="w-full pl-11 pr-4 py-3 bg-white/50 border border-slate-200/60 rounded-2xl text-slate-900 focus:outline-none focus:ring-4 focus:ring-[#064e3b]/10 focus:border-[#064e3b] transition-all duration-300 shadow-sm appearance-none cursor-pointer"
                                >
                                    <option value="" disabled className="text-slate-400">Select a service...</option>
                                    {services?.map((s) => (
                                        <option key={s.id} value={s.name} className="text-slate-900 bg-white">
                                            {s.name} (${s.price})
                                        </option>
                                    ))}
                                </select>
                                <SelectArrow />
                            </div>
                        </div>

                        {/* Date, Time & Duration */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                            <div className="space-y-1.5">
                                <label htmlFor="date" className="text-sm font-bold text-slate-700 ml-1">
                                    Date <span className="text-emerald-500">*</span>
                                </label>
                                <div className="relative">
                                    <div className="absolute left-0 pl-4 inset-y-0 flex items-center pointer-events-none">
                                        <Calendar className="h-5 w-5 text-slate-400" />
                                    </div>
                                    <input
                                        id="date"
                                        type="date"
                                        value={formData.date ? new Date(formData.date.getTime() - formData.date.getTimezoneOffset() * 60000).toISOString().split('T')[0] : ''}
                                        onChange={(e) => setFormData({ ...formData, date: e.target.value ? new Date(e.target.value) : undefined })}
                                        required
                                        className="w-full pl-11 pr-4 py-3 bg-white/50 border border-slate-200/60 rounded-2xl text-slate-900 focus:outline-none focus:ring-4 focus:ring-[#064e3b]/10 focus:border-[#064e3b] transition-all duration-300 shadow-sm cursor-pointer"
                                    />
                                </div>
                            </div>
                            <div className="space-y-1.5">
                                <label htmlFor="time" className="text-sm font-bold text-slate-700 ml-1">
                                    Time <span className="text-emerald-500">*</span>
                                </label>
                                <div className="relative">
                                    <div className="absolute left-0 pl-4 inset-y-0 flex items-center pointer-events-none">
                                        <Clock className="h-5 w-5 text-slate-400" />
                                    </div>
                                    <select
                                        id="time"
                                        value={formData.time}
                                        onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                                        required
                                        className="w-full pl-11 pr-4 py-3 bg-white/50 border border-slate-200/60 rounded-2xl text-slate-900 focus:outline-none focus:ring-4 focus:ring-[#064e3b]/10 focus:border-[#064e3b] transition-all duration-300 shadow-sm appearance-none cursor-pointer"
                                    >
                                        {timeSlots.map((slot) => (
                                            <option key={slot.value} value={slot.value} className="text-slate-900 bg-white">
                                                {slot.label}
                                            </option>
                                        ))}
                                    </select>
                                    <SelectArrow />
                                </div>
                            </div>
                            
                        </div>

                        {/* Notes */}
                        <div className="space-y-1.5">
                            <label htmlFor="notes" className="text-sm font-bold text-slate-700 ml-1">
                                Notes
                            </label>
                            <div className="relative">
                                <div className="absolute left-0 pl-4 top-3.5 flex pointer-events-none">
                                    <AlignLeft className="h-5 w-5 text-slate-400" />
                                </div>
                                <textarea
                                    id="notes"
                                    value={formData.notes}
                                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                    placeholder="Any special requests or details..."
                                    rows={3}
                                    className="w-full pl-11 pr-4 py-3 bg-white/50 border border-slate-200/60 rounded-2xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-[#064e3b]/10 focus:border-[#064e3b] transition-all duration-300 shadow-sm resize-none"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="mt-8 flex gap-3">
                        <button type="button" onClick={() => onOpenChange(false)} disabled={isLoading} className="flex-1 py-3.5 px-6 rounded-2xl font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors duration-300">
                            Cancel
                        </button>
                        <button type="submit" disabled={isLoading} className="flex-1 bg-[#064e3b] hover:bg-[#064e3b]/90 text-white font-medium py-3.5 px-6 rounded-2xl transition-all duration-300 active:scale-[0.98] flex items-center justify-center gap-2 shadow-lg shadow-[#064e3b]/20 disabled:opacity-50">
                            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                            {mode === "create" ? "Book Appointment" : "Save Changes"}
                        </button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
