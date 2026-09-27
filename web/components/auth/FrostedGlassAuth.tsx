"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Eye, EyeOff, Mail, Lock, User, ArrowLeft, Check, Shield, X } from "lucide-react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"

const LoginSchema = z.object({
    email: z.string().email("Invalid email address").max(254),
    password: z.string().min(8, "Password must be at least 8 characters").max(128),
})

const RegisterSchema = z.object({
    email: z.string().email("Invalid email address").max(254),
    password: z.string()
        .min(12, "Password must be at least 12 characters")
        .max(128)
        .regex(/[A-Z]/, "Must contain an uppercase letter")
        .regex(/[a-z]/, "Must contain a lowercase letter")
        .regex(/\d/, "Must contain a number")
        .regex(/[!@#$%^&*(),.?":{}|<>]/, "Must contain a special character"),
    confirmPassword: z.string(),
    name: z.string().min(1, "Name is required").max(100),
    business_name: z.string().min(1, "Business name is required").max(200),
    phone: z.string().max(20).optional(),
}).refine((d) => d.password === d.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
})

type AuthStep = "login" | "signup" | "forgot-password" | "reset-password" | "otp" | "success" | "pending"
type AuthMode = "login" | "signup"

interface PasswordRequirement {
    label: string
    test: (password: string) => boolean
}

const passwordRequirements: PasswordRequirement[] = [
    { label: "At least 8 characters", test: (pwd) => pwd.length >= 8 },
    { label: "One uppercase letter", test: (pwd) => /[A-Z]/.test(pwd) },
    { label: "One lowercase letter", test: (pwd) => /[a-z]/.test(pwd) },
    { label: "One number", test: (pwd) => /\d/.test(pwd) },
    { label: "One special character", test: (pwd) => /[!@#$%^&*(),.?":{}|<>]/.test(pwd) },
]

interface FrostedGlassAuthProps {
    initialMode?: AuthMode
}

export function FrostedGlassAuth({ initialMode = "login" }: FrostedGlassAuthProps) {
    const router = useRouter()
    const { login, register } = useAuth()
    const [step, setStep] = useState<AuthStep>(initialMode)
    const [mode, setMode] = useState<AuthMode>(initialMode)
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const [formData, setFormData] = useState({
        email: "",
        password: "",
        confirmPassword: "",
        name: "",
        business_name: "",
        phone: "",
        otp: ["", "", "", "", "", ""],
    })

    // Sync internal state if initialMode changes
    useEffect(() => {
        setMode(initialMode)
        setStep(initialMode)
    }, [initialMode])

    const handleInputChange = (field: string, value: string) => {
        setFormData((prev) => ({ ...prev, [field]: value }))
    }

    const handleOtpChange = (index: number, value: string) => {
        if (value.length <= 1 && /^\d*$/.test(value)) {
            const newOtp = [...formData.otp]
            newOtp[index] = value
            setFormData((prev) => ({ ...prev, otp: newOtp }))

            // Auto-focus next input
            if (value && index < 5) {
                const nextInput = document.getElementById(`otp-${index + 1}`)
                nextInput?.focus()
            }
        }
    }

    const getPasswordStrength = (password: string) => {
        const passedRequirements = passwordRequirements.filter((req) => req.test(password)).length
        if (passedRequirements === 0) return { strength: 0, label: "", color: "" }
        // Using shades of Cyan for all strength levels to match theme
        if (passedRequirements <= 2) return { strength: 25, label: "Weak", color: "bg-red-500" }
        if (passedRequirements <= 3) return { strength: 50, label: "Fair", color: "bg-yellow-500" }
        if (passedRequirements <= 4) return { strength: 75, label: "Good", color: "bg-[#4ade80]" }
        return { strength: 100, label: "Strong", color: "bg-[#2C7A44] shadow-[0_0_10px_rgba(44,122,68,0.5)]" }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)

        // Client-side validation before hitting the network
        if (step === "login") {
            const result = LoginSchema.safeParse({ email: formData.email, password: formData.password })
            if (!result.success) {
                alert(result.error.errors[0].message)
                setIsLoading(false)
                return
            }
        } else if (step === "signup") {
            const result = RegisterSchema.safeParse(formData)
            if (!result.success) {
                alert(result.error.errors[0].message)
                setIsLoading(false)
                return
            }
        }

        try {
            if (step === "login") {
                await login({
                    username: formData.email,
                    password: formData.password
                });
                // Redirect is handled in AuthContext
            } else if (step === "signup") {
                // Register returns a pending response
                try {
                    await register({
                        email: formData.email,
                        username: formData.email,
                        password: formData.password,
                        full_name: formData.name,
                        business_name: formData.business_name,
                        phone: formData.phone,
                        role: "owner"
                    });
                } catch (error: any) {
                    // Check if it's a pending approval error
                    if (error.message && error.message.startsWith('PENDING_APPROVAL:')) {
                        // Show pending screen
                        setStep("pending");
                        return; // Don't throw, just show pending screen
                    }
                    // Re-throw other errors
                    throw error;
                }
            } else if (step === "forgot-password") {
                // TODO: Implement forgot password API
                setStep("reset-password")
            } else if (step === "reset-password") {
                // TODO: Implement reset password API
                setStep("success")
            } else if (step === "otp") {
                setStep("success")
            }
        } catch (error: any) {
            console.error("Auth error:", error);
            // Better error messages for users
            let errorMessage = "An error occurred. Please try again.";
            if (error.response?.data?.detail) {
                errorMessage = error.response.data.detail;
            } else if (error.message) {
                errorMessage = error.message;
            }

            // Show specific errors for common issues
            if (errorMessage.includes("already registered") || errorMessage.includes("already taken")) {
                errorMessage = "This email or username is already registered. Please try logging in instead.";
            } else if (errorMessage.includes("Incorrect username") || errorMessage.includes("Incorrect password")) {
                errorMessage = "Invalid email or password. Please check your credentials.";
            }

            alert(errorMessage);
        } finally {
            setIsLoading(false)
        }
    }

    const switchMode = (newMode: AuthMode) => {
        setMode(newMode)
        setStep(newMode)
        setFormData({ email: "", password: "", confirmPassword: "", name: "", business_name: "", phone: "", otp: ["", "", "", "", "", ""] })
        // Update URL without full reload
        window.history.pushState({}, "", `/${newMode}`)
    }

    const resetToLogin = () => {
        setStep("login")
        setMode("login")
        setFormData({ email: "", password: "", confirmPassword: "", name: "", business_name: "", phone: "", otp: ["", "", "", "", "", ""] })
        window.history.pushState({}, "", "/login")
    }

    const goToForgotPassword = () => {
        setStep("forgot-password")
        setFormData((prev) => ({ ...prev, password: "", confirmPassword: "", name: "", business_name: "", phone: "", otp: ["", "", "", "", "", ""] }))
    }

    const getCardHeight = () => {
        switch (step) {
            case "login":
                return "h-[480px]"
            case "signup":
                return "h-[680px]"
            case "forgot-password":
                return "h-[380px]"
            case "reset-password":
                return "h-[520px]"
            case "otp":
                return "h-[380px]"
            case "pending":
                return "h-[420px]"
            case "success":
                return "h-[320px]"
            default:
                return "h-[480px]"
        }
    }

    const passwordStrength = getPasswordStrength(formData.password)
    const isSignupValid =
        step === "signup" &&
        formData.name &&
        formData.business_name &&
        formData.phone &&
        formData.email &&
        formData.password &&
        formData.confirmPassword &&
        formData.password === formData.confirmPassword &&
        passwordRequirements.every((req) => req.test(formData.password))

    return (
        <div className={`w-[450px] max-w-full transition-all duration-700 ease-out ${getCardHeight()}`}>
            <div className="relative h-full">
                {/* Glass morphism card - Darker Background for Contrast */}
                <div className="absolute inset-0 bg-[#05100a]/80 backdrop-blur-xl rounded-3xl border border-white/10 shadow-2xl">
                    {/* Subtle gradient overlay */}
                    <div className="absolute inset-0 bg-gradient-to-br from-[#2C7A44]/20 via-transparent to-transparent rounded-3xl" />
                </div>

                {/* Content */}
                <div className="relative h-full p-8 flex flex-col">
                    {step === "login" && (
                        <div className="flex-1 flex flex-col justify-center space-y-6">
                            <div className="text-center space-y-2">
                                <h1 className="text-2xl font-semibold text-white">Welcome Back</h1>
                                <p className="text-slate-300">Sign in to your account</p>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="email" className="text-slate-200">
                                        Email or Username
                                    </Label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            id="email"
                                            type="text"
                                            value={formData.email}
                                            onChange={(e) => handleInputChange("email", e.target.value)}
                                            className="pl-10 bg-black/40 border-white/10 text-white placeholder:text-slate-500 focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20"
                                            placeholder="Enter your email or username"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="password" className="text-slate-200">
                                        Password
                                    </Label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            id="password"
                                            type={showPassword ? "text" : "password"}
                                            value={formData.password}
                                            onChange={(e) => handleInputChange("password", e.target.value)}
                                            className="pl-10 pr-10 bg-black/40 border-white/10 text-white placeholder:text-slate-500 focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20"
                                            placeholder="Enter your password"
                                            required
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
                                        >
                                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                        </button>
                                    </div>
                                </div>

                                <div className="text-right">
                                    <button
                                        type="button"
                                        onClick={goToForgotPassword}
                                        className="text-[#4ade80] hover:text-[#2C7A44] text-sm transition-colors"
                                    >
                                        Forgot password?
                                    </button>
                                </div>

                                <Button
                                    type="submit"
                                    disabled={isLoading}
                                    className="w-full bg-[#2C7A44] hover:bg-[#246337] text-white border border-[#2C7A44]/30 h-11 rounded-xl font-medium transition-all duration-200 shadow-[0_0_15px_rgba(44,122,68,0.3)] hover:shadow-[0_0_20px_rgba(44,122,68,0.5)]"
                                >
                                    {isLoading ? "Signing in..." : "Sign In"}
                                </Button>
                            </form>

                            <div className="text-center">
                                <button
                                    onClick={() => switchMode("signup")}
                                    className="text-slate-300 hover:text-white text-sm transition-colors"
                                >
                                    {"Don't have an account? "} <span className="text-[#4ade80] hover:text-[#2C7A44]">Sign up</span>
                                </button>
                            </div>
                        </div>
                    )}

                    {step === "signup" && (
                        <div className="flex-1 flex flex-col justify-center space-y-6">
                            <div className="text-center space-y-2">
                                <h1 className="text-2xl font-semibold text-white">Create Account</h1>
                                <p className="text-slate-300">Join us today</p>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="name" className="text-slate-200">
                                        Full Name
                                    </Label>
                                    <div className="relative">
                                        <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            id="name"
                                            type="text"
                                            value={formData.name}
                                            onChange={(e) => handleInputChange("name", e.target.value)}
                                            className="pl-10 bg-black/40 border-white/10 text-white placeholder:text-slate-500 focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20"
                                            placeholder="Enter your full name"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="business_name" className="text-slate-200">
                                        Business Name
                                    </Label>
                                    <div className="relative">
                                        <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            id="business_name"
                                            type="text"
                                            value={formData.business_name}
                                            onChange={(e) => handleInputChange("business_name", e.target.value)}
                                            className="pl-10 bg-black/40 border-white/10 text-white placeholder:text-slate-500 focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20"
                                            placeholder="Enter your business name"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="phone" className="text-slate-200">
                                        Phone Number
                                    </Label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            id="phone"
                                            type="tel"
                                            value={formData.phone}
                                            onChange={(e) => handleInputChange("phone", e.target.value)}
                                            className="pl-10 bg-black/40 border-white/10 text-white placeholder:text-slate-500 focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20"
                                            placeholder="+1234567890"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="signup-email" className="text-slate-200">
                                        Email
                                    </Label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            id="signup-email"
                                            type="email"
                                            value={formData.email}
                                            onChange={(e) => handleInputChange("email", e.target.value)}
                                            className="pl-10 bg-black/40 border-white/10 text-white placeholder:text-slate-500 focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20"
                                            placeholder="Enter your email"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="signup-password" className="text-slate-200">
                                        Password
                                    </Label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            id="signup-password"
                                            type={showPassword ? "text" : "password"}
                                            value={formData.password}
                                            onChange={(e) => handleInputChange("password", e.target.value)}
                                            className="pl-10 pr-10 bg-black/40 border-white/10 text-white placeholder:text-slate-500 focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20"
                                            placeholder="Create a password"
                                            required
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
                                        >
                                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                        </button>
                                    </div>

                                    {formData.password && (
                                        <div className="space-y-2">
                                            <div className="flex items-center justify-between">
                                                <span className="text-xs text-slate-400">Password strength</span>
                                                <span
                                                    className={`text-xs font-medium ${passwordStrength.strength === 100
                                                        ? "text-[#4ade80]"
                                                        : passwordStrength.strength >= 75
                                                            ? "text-[#2C7A44]"
                                                            : passwordStrength.strength >= 50
                                                                ? "text-yellow-500"
                                                                : "text-red-500"
                                                        }`}
                                                >
                                                    {passwordStrength.label}
                                                </span>
                                            </div>
                                            <div className="w-full bg-white/5 rounded-full h-1.5">
                                                <div
                                                    className={`h-1.5 rounded-full transition-all duration-300 ${passwordStrength.color}`}
                                                    style={{ width: `${passwordStrength.strength}%` }}
                                                />
                                            </div>
                                            <div className="space-y-1">
                                                {passwordRequirements.map((req, index) => (
                                                    <div key={index} className="flex items-center space-x-2">
                                                        <div
                                                            className={`w-1.5 h-1.5 rounded-full ${req.test(formData.password) ? "bg-[#2C7A44]" : "bg-white/10"
                                                                }`}
                                                        />
                                                        <span
                                                            className={`text-xs ${req.test(formData.password) ? "text-slate-300" : "text-slate-600"}`}
                                                        >
                                                            {req.label}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="confirm-password" className="text-slate-200">
                                        Confirm Password
                                    </Label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            id="confirm-password"
                                            type={showConfirmPassword ? "text" : "password"}
                                            value={formData.confirmPassword}
                                            onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
                                            className="pl-10 pr-10 bg-black/40 border-white/10 text-white placeholder:text-slate-500 focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20"
                                            placeholder="Confirm your password"
                                            required
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
                                        >
                                            {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                        </button>
                                    </div>
                                    {formData.confirmPassword && formData.password !== formData.confirmPassword && (
                                        <p className="text-xs text-red-400">Passwords do not match</p>
                                    )}
                                </div>

                                <Button
                                    type="submit"
                                    disabled={isLoading || !isSignupValid}
                                    className="w-full bg-[#2C7A44] hover:bg-[#246337] text-white border border-[#2C7A44]/30 h-11 rounded-xl font-medium transition-all duration-200 shadow-[0_0_15px_rgba(44,122,68,0.3)] hover:shadow-[0_0_20px_rgba(44,122,68,0.5)] disabled:opacity-50 disabled:shadow-none"
                                >
                                    {isLoading ? "Creating account..." : "Sign Up"}
                                </Button>
                            </form>

                            <div className="text-center">
                                <button
                                    onClick={() => switchMode("login")}
                                    className="text-slate-300 hover:text-white text-sm transition-colors"
                                >
                                    Already have an account? <span className="text-[#4ade80] hover:text-[#2C7A44]">Sign in</span>
                                </button>
                            </div>
                        </div>
                    )}

                    {step === "forgot-password" && (
                        <div className="flex-1 flex flex-col justify-center space-y-6">
                            <button
                                onClick={resetToLogin}
                                className="absolute top-6 left-6 text-slate-400 hover:text-white transition-colors"
                            >
                                <ArrowLeft className="w-5 h-5" />
                            </button>

                            <div className="text-center space-y-2">
                                <h1 className="text-2xl font-semibold text-white">Reset Password</h1>
                                <p className="text-slate-300">Enter your email to receive reset instructions</p>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="reset-email" className="text-slate-200">
                                        Email
                                    </Label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            id="reset-email"
                                            type="email"
                                            value={formData.email}
                                            onChange={(e) => handleInputChange("email", e.target.value)}
                                            className="pl-10 bg-black/40 border-white/10 text-white placeholder:text-slate-500 focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20"
                                            placeholder="Enter your email"
                                            required
                                        />
                                    </div>
                                </div>

                                <Button
                                    type="submit"
                                    disabled={isLoading}
                                    className="w-full bg-[#2C7A44] hover:bg-[#246337] text-white border border-[#2C7A44]/30 h-11 rounded-xl font-medium transition-all duration-200 shadow-[0_0_15px_rgba(44,122,68,0.3)] hover:shadow-[0_0_20px_rgba(44,122,68,0.5)]"
                                >
                                    {isLoading ? "Sending..." : "Send Reset Link"}
                                </Button>
                            </form>
                        </div>
                    )}

                    {step === "reset-password" && (
                        <div className="flex-1 flex flex-col justify-center space-y-6">
                            <button
                                onClick={() => setStep("forgot-password")}
                                className="absolute top-6 left-6 text-slate-400 hover:text-white transition-colors"
                            >
                                <ArrowLeft className="w-5 h-5" />
                            </button>

                            <div className="text-center space-y-2">
                                <div className="w-12 h-12 bg-[#2C7A44]/10 backdrop-blur-sm border border-[#2C7A44]/20 rounded-full flex items-center justify-center mx-auto">
                                    <Shield className="w-6 h-6 text-[#4ade80]" />
                                </div>
                                <h1 className="text-2xl font-semibold text-white">Create New Password</h1>
                                <p className="text-slate-300">Enter your new password below</p>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="new-password" className="text-slate-200">
                                        New Password
                                    </Label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            id="new-password"
                                            type={showPassword ? "text" : "password"}
                                            value={formData.password}
                                            onChange={(e) => handleInputChange("password", e.target.value)}
                                            className="pl-10 pr-10 bg-black/40 border-white/10 text-white placeholder:text-slate-500 focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20"
                                            placeholder="Enter new password"
                                            required
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
                                        >
                                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                        </button>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="confirm-new-password" className="text-slate-200">
                                        Confirm New Password
                                    </Label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            id="confirm-new-password"
                                            type={showConfirmPassword ? "text" : "password"}
                                            value={formData.confirmPassword}
                                            onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
                                            className="pl-10 pr-10 bg-black/40 border-white/10 text-white placeholder:text-slate-500 focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20"
                                            placeholder="Confirm new password"
                                            required
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
                                        >
                                            {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                        </button>
                                    </div>
                                    {formData.confirmPassword && formData.password !== formData.confirmPassword && (
                                        <p className="text-xs text-red-400">Passwords do not match</p>
                                    )}
                                </div>

                                <Button
                                    type="submit"
                                    disabled={isLoading || !formData.password || formData.password !== formData.confirmPassword}
                                    className="w-full bg-[#2C7A44] hover:bg-[#246337] text-white border border-[#2C7A44]/30 h-11 rounded-xl font-medium transition-all duration-200 shadow-[0_0_15px_rgba(44,122,68,0.3)] hover:shadow-[0_0_20px_rgba(44,122,68,0.5)] disabled:opacity-50"
                                >
                                    {isLoading ? "Updating..." : "Update Password"}
                                </Button>
                            </form>
                        </div>
                    )}

                    {step === "otp" && (
                        <div className="flex-1 flex flex-col justify-center space-y-6">
                            <button
                                onClick={() => setStep(mode)}
                                className="absolute top-6 left-6 text-slate-400 hover:text-white transition-colors"
                            >
                                <ArrowLeft className="w-5 h-5" />
                            </button>

                            <div className="text-center space-y-2">
                                <h1 className="text-2xl font-semibold text-white">Verify Your Email</h1>
                                <p className="text-slate-300">Enter the 6-digit code sent to</p>
                                <p className="text-white font-medium">{formData.email}</p>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div className="flex justify-center space-x-3">
                                    {formData.otp.map((digit, index) => (
                                        <Input
                                            key={index}
                                            id={`otp-${index}`}
                                            type="text"
                                            value={digit}
                                            onChange={(e) => handleOtpChange(index, e.target.value)}
                                            className="w-12 h-12 text-center text-lg font-semibold bg-black/40 border-white/10 text-white focus:border-[#2C7A44]/50 focus:ring-[#2C7A44]/20 rounded-xl"
                                            maxLength={1}
                                        />
                                    ))}
                                </div>

                                <Button
                                    type="submit"
                                    disabled={isLoading || formData.otp.some((digit) => !digit)}
                                    className="w-full bg-[#2C7A44] hover:bg-[#246337] text-white border border-[#2C7A44]/30 h-11 rounded-xl font-medium transition-all duration-200 shadow-[0_0_15px_rgba(44,122,68,0.3)] hover:shadow-[0_0_20px_rgba(44,122,68,0.5)]"
                                >
                                    {isLoading ? "Verifying..." : "Verify Code"}
                                </Button>
                            </form>

                            <div className="text-center">
                                <button className="text-slate-400 hover:text-white text-sm transition-colors">Resend code</button>
                            </div>
                        </div>
                    )}

                    {step === "pending" && (
                        <div className="flex-1 flex flex-col justify-center items-center space-y-6">
                            <div className="w-16 h-16 bg-[#2C7A44]/10 backdrop-blur-sm border border-[#2C7A44]/20 rounded-full flex items-center justify-center">
                                <Shield className="w-8 h-8 text-[#4ade80]" />
                            </div>

                            <div className="text-center space-y-2">
                                <h1 className="text-2xl font-semibold text-white">
                                    Account Under Review
                                </h1>
                                <p className="text-slate-300 max-w-sm">
                                    Your account is under review. You will be notified once approved.
                                </p>
                                <p className="text-slate-400 text-sm mt-4">
                                    Registered email: <span className="text-white">{formData.email}</span>
                                </p>
                            </div>

                            <Button
                                onClick={resetToLogin}
                                className="w-full bg-[#2C7A44] hover:bg-[#246337] text-white border border-[#2C7A44]/30 h-11 rounded-xl font-medium transition-all duration-200 shadow-[0_0_15px_rgba(44,122,68,0.3)] hover:shadow-[0_0_20px_rgba(44,122,68,0.5)]"
                            >
                                Back to Login
                            </Button>
                        </div>
                    )}

                    {step === "success" && (
                        <div className="flex-1 flex flex-col justify-center items-center space-y-6">
                            <button
                                onClick={resetToLogin}
                                className="absolute top-6 right-6 text-slate-400 hover:text-white transition-colors p-1 rounded-full hover:bg-white/10"
                            >
                                <X className="w-5 h-5" />
                            </button>

                            <div className="w-16 h-16 bg-[#2C7A44]/10 backdrop-blur-sm border border-[#2C7A44]/20 rounded-full flex items-center justify-center">
                                <Check className="w-8 h-8 text-[#4ade80]" />
                            </div>

                            <div className="text-center space-y-2">
                                <h1 className="text-2xl font-semibold text-white">
                                    {step === "success" && mode === "signup" ? "Welcome!" : "Success!"}
                                </h1>
                                <p className="text-slate-300">
                                    {step === "success" && mode === "signup"
                                        ? "Your account has been verified successfully"
                                        : "Your password has been reset successfully"}
                                </p>
                            </div>

                            <Button
                                onClick={() => router.push("/dashboard")}
                                className="w-full bg-[#2C7A44] hover:bg-[#246337] text-white border border-[#2C7A44]/30 h-11 rounded-xl font-medium transition-all duration-200 shadow-[0_0_15px_rgba(44,122,68,0.3)] hover:shadow-[0_0_20px_rgba(44,122,68,0.5)]"
                            >
                                Go to Dashboard
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
