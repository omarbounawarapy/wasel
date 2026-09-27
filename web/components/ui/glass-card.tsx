"use client"

import { cn } from "@/lib/utils"
import type React from "react"

interface GlassCardProps {
    children: React.ReactNode
    className?: string
    variant?: "card" | "button" | "panel"
    glowColor?: string
    showGlow?: boolean
    hoverScale?: boolean
    onClick?: () => void
}

/**
 * Reusable glass effect card/panel component with gradient glow lines
 * Provides consistent premium design across all sections
 */
export function GlassCard({
    children,
    className,
    variant = "card",
    glowColor = "#0891b2",
    showGlow = true,
    hoverScale = true,
    onClick,
}: GlassCardProps) {
    const baseStyles = "group relative backdrop-blur-xl border transition-all duration-300"

    const variantStyles = {
        card: "rounded-3xl border-white/10 bg-slate-950/70 shadow-2xl p-8",
        button: "rounded-full border-white/20 bg-white/5 px-6 py-2 text-sm shadow-lg hover:shadow-xl active:scale-95",
        panel: "rounded-2xl border-white/10 bg-slate-950/70 shadow-xl p-6",
    }

    const hoverStyles = hoverScale ? "hover:scale-[1.02]" : ""

    return (
        <div
            className={cn(
                baseStyles,
                variantStyles[variant],
                hoverStyles,
                onClick && "cursor-pointer",
                className
            )}
            onClick={onClick}
        >
            {/* Top gradient glow line */}
            {showGlow && (
                <div
                    className="absolute inset-x-0 -top-px mx-auto h-0.5 w-1/2 bg-gradient-to-r from-transparent via-current to-transparent shadow-2xl transition-all duration-500 group-hover:w-3/4"
                    style={{ color: glowColor }}
                />
            )}

            {/* Bottom gradient glow line */}
            {showGlow && (
                <div
                    className="absolute inset-x-0 -bottom-px mx-auto h-0.5 w-1/2 bg-gradient-to-r from-transparent via-current to-transparent shadow-2xl transition-all duration-500 group-hover:w-3/4"
                    style={{ color: glowColor }}
                />
            )}

            {/* Subtle gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-transparent rounded-[inherit] pointer-events-none" />

            {/* Content wrapper */}
            <div className="relative z-10">{children}</div>
        </div>
    )
}
