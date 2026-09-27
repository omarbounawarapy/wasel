import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { servicesApi } from "@/lib/api-endpoints";
import { ServiceCreate, ServiceResponse } from "@/lib/types";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { Loader2, Type, AlignLeft, DollarSign } from "lucide-react";

interface ServiceFormModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    service?: ServiceResponse | null;
    mode: "create" | "edit";
}

export default function ServiceFormModal({
    open,
    onOpenChange,
    service,
    mode,
}: ServiceFormModalProps) {
    const queryClient = useQueryClient();
    const [formData, setFormData] = useState<ServiceCreate & { active: boolean }>({
        name: "",
        description: "",
        price: 0,
        active: true,
    });

    useEffect(() => {
        if (mode === "edit" && service) {
            setFormData({
                name: service.name,
                description: service.description || "",
                price: service.price,
                active: service.active,
            });
        } else {
            setFormData({ name: "", description: "", price: 0, active: true });
        }
    }, [mode, service, open]);

    const createMutation = useMutation({
        mutationFn: servicesApi.create,
        onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["services"] }); toast.success("Service created successfully!"); onOpenChange(false); },
        onError: (error: any) => {
            if (error.response?.data?.detail) {
                const detail = error.response.data.detail;
                if (Array.isArray(detail)) { toast.error(detail.map((e: any) => `${e.loc?.join(' -> ') || 'Error'}: ${e.msg}`).join(', ')); }
                else if (typeof detail === 'string') { toast.error(detail); }
                else { toast.error("Failed to create service"); }
            } else { toast.error("Failed to create service"); }
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: ServiceCreate }) => servicesApi.update(id, data),
        onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["services"] }); toast.success("Service updated successfully!"); onOpenChange(false); },
        onError: (error: any) => {
            if (error.response?.data?.detail) {
                const detail = error.response.data.detail;
                if (Array.isArray(detail)) { toast.error(detail.map((e: any) => `${e.loc?.join(' -> ') || 'Error'}: ${e.msg}`).join(', ')); }
                else if (typeof detail === 'string') { toast.error(detail); }
                else { toast.error("Failed to update service"); }
            } else { toast.error("Failed to update service"); }
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name || formData.price < 0) { toast.error("Please fill in all required fields correctly"); return; }
        const submitData: ServiceCreate = { name: formData.name, description: formData.description, price: formData.price, active: formData.active };
        if (mode === "create") { createMutation.mutate(submitData); }
        else if (service?.id) { updateMutation.mutate({ id: service.id, data: submitData }); }
    };

    const isLoading = createMutation.isPending || updateMutation.isPending;

    const fields = [
        { id: "name", label: "Service Name", required: true, type: "text", placeholder: "e.g., Haircut, Consultation, Massage", icon: Type },
        { id: "description", label: "Description", required: false, type: "textarea", placeholder: "Brief description of the service...", icon: AlignLeft },
        { id: "price", label: "Price ($)", required: true, type: "number", placeholder: "", min: "0", step: "0.01", icon: DollarSign },
    ];

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md p-0 rounded-[2.5rem] overflow-hidden border-0 shadow-2xl">
                <div className="absolute top-0 inset-x-0 h-2 bg-gradient-to-r from-[#064e3b] to-emerald-500" />
                
                <form onSubmit={handleSubmit} className="p-8">
                    <div className="mb-8">
                        <DialogHeader>
                            <DialogTitle className="text-2xl font-black text-slate-900 mb-1">
                                {mode === "create" ? "Add New Service" : "Edit Service"}
                            </DialogTitle>
                            <DialogDescription className="text-slate-500 font-medium text-sm">
                                {mode === "create" ? "Create a new offering for your clients." : "Update service details below."}
                            </DialogDescription>
                        </DialogHeader>
                    </div>

                    <div className="space-y-5">
                        {fields.map((field) => (
                            <div key={field.id} className="space-y-1.5">
                                <label htmlFor={field.id} className="text-sm font-bold text-slate-700 ml-1">
                                    {field.label} {field.required && <span className="text-emerald-500">*</span>}
                                </label>
                                <div className="relative">
                                    <div className={`absolute left-0 pl-4 flex pointer-events-none ${field.type === "textarea" ? "top-3.5" : "inset-y-0 items-center"}`}>
                                        <field.icon className="h-5 w-5 text-slate-400" />
                                    </div>
                                    {field.type === "textarea" ? (
                                        <textarea
                                            id={field.id}
                                            value={(formData as any)[field.id]}
                                            onChange={(e) => setFormData({ ...formData, [field.id]: e.target.value })}
                                            placeholder={field.placeholder}
                                            rows={3}
                                            className="w-full pl-11 pr-4 py-3 bg-white/50 border border-slate-200/60 rounded-2xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-[#064e3b]/10 focus:border-[#064e3b] transition-all duration-300 shadow-sm resize-none"
                                        />
                                    ) : (
                                        <input
                                            id={field.id}
                                            type={field.type}
                                            min={field.min}
                                            step={field.step}
                                            value={(formData as any)[field.id]}
                                            onChange={(e) => setFormData({ ...formData, [field.id]: field.type === "number" ? (field.step === "0.01" ? parseFloat(e.target.value) || 0 : parseInt(e.target.value) || 0) : e.target.value })}
                                            placeholder={field.placeholder}
                                            required={field.required}
                                            className="w-full pl-11 pr-4 py-3 bg-white/50 border border-slate-200/60 rounded-2xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-[#064e3b]/10 focus:border-[#064e3b] transition-all duration-300 shadow-sm"
                                        />
                                    )}
                                </div>
                            </div>
                        ))}

                        {/* Active Toggle */}
                        <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-100 rounded-2xl">
                            <div className="space-y-0.5">
                                <label htmlFor="active" className="text-sm font-bold text-slate-700 cursor-pointer">Service Status</label>
                                <p className="text-xs font-medium text-slate-500">Make this service visible to clients</p>
                            </div>
                            <Switch
                                id="active"
                                checked={formData.active}
                                onCheckedChange={(checked) => setFormData({ ...formData, active: checked as boolean })}
                                className="data-[state=checked]:bg-[#064e3b]"
                            />
                        </div>
                    </div>

                    <div className="mt-8 flex gap-3">
                        <button type="button" onClick={() => onOpenChange(false)} disabled={isLoading} className="flex-1 py-3.5 px-6 rounded-2xl font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors duration-300">
                            Cancel
                        </button>
                        <button type="submit" disabled={isLoading} className="flex-1 bg-[#064e3b] hover:bg-[#064e3b]/90 text-white font-medium py-3.5 px-6 rounded-2xl transition-all duration-300 active:scale-[0.98] flex items-center justify-center gap-2 shadow-lg shadow-[#064e3b]/20 disabled:opacity-50">
                            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                            {mode === "create" ? "Add Service" : "Save Changes"}
                        </button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
