'use client'

import { useToast } from '@/hooks/use-toast'
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from '@/components/ui/toast'

export function Toaster() {
  const { toasts } = useToast()

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, ...props }) {
        return (
          <Toast key={id} {...props} className={`bg-gradient-to-b from-[#156e40] via-[#0a4c2f] to-[#052b19] rounded-[20px] p-5 relative overflow-hidden text-white shadow-xl shadow-green-900/20 border border-[#1b8550]/20 ${props.variant === 'destructive' ? 'from-red-900 via-red-800 to-red-950 border-red-500/30' : ''}`}>
            <div className="absolute -top-10 -left-10 w-32 h-32 bg-[#21a05e] rounded-full blur-3xl opacity-30 pointer-events-none"></div>
            <svg className="absolute inset-0 w-full h-full opacity-20 pointer-events-none" preserveAspectRatio="none" viewBox="0 0 100 100">
              <path d="M0,50 Q25,20 50,50 T100,50 L100,100 L0,100 Z" fill="#48a074"></path>
              <path d="M0,70 Q25,40 50,70 T100,70 L100,100 L0,100 Z" fill="#2f7351"></path>
            </svg>
            <div className="grid gap-1 relative z-10 w-full pr-6">
              {title && <ToastTitle className="text-white text-[15px]">{title}</ToastTitle>}
              {description && (
                <ToastDescription className="text-white/80">{description}</ToastDescription>
              )}
            </div>
            {action}
            <ToastClose className="text-white/60 hover:text-white relative z-10 mt-1 right-3 top-3 focus:ring-green-400" />
          </Toast>
        )
      })}
      <ToastViewport />
    </ToastProvider>
  )
}
