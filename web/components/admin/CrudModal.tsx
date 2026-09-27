import React from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

interface CrudModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    title: string;
    description?: string;
    children: React.ReactNode;
}

export function CrudModal({
    open,
    onOpenChange,
    title,
    description,
    children
}: CrudModalProps) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-hidden p-0 rounded-[24px]" aria-describedby={undefined}>
                <div className="px-6 pt-6 pb-4 border-b border-gray-100">
                    <DialogHeader>
                        <DialogTitle className="text-xl font-bold text-gray-900">{title}</DialogTitle>
                        {description && (
                            <DialogDescription className="text-sm text-gray-500">
                                {description}
                            </DialogDescription>
                        )}
                    </DialogHeader>
                </div>
                <div className="px-6 pb-6 pt-4 overflow-y-auto max-h-[70vh]">
                    {children}
                </div>
            </DialogContent>
        </Dialog>
    );
}
