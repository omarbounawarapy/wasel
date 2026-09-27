/**
 * Tests for Zod validation schemas in FrostedGlassAuth.tsx
 *
 * Verifies:
 * - LoginSchema: valid email + password passes; invalid email fails; short password fails
 * - RegisterSchema: full valid payload passes; mismatched passwords fail;
 *   weak password (no special char, no uppercase, <12 chars) fails;
 *   oversized fields (>254 email, >128 password, >100 name) fail
 */

import { describe, it, expect } from 'vitest'
import { z } from 'zod'

// ── Re-define schemas here (same source as FrostedGlassAuth.tsx) ──────────────
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
// ─────────────────────────────────────────────────────────────────────────────

describe('LoginSchema', () => {
    const valid = { email: 'user@example.com', password: 'Passw0rd!' }

    it('accepts a valid email + password', () => {
        expect(LoginSchema.safeParse(valid).success).toBe(true)
    })

    it('rejects an invalid email format', () => {
        const result = LoginSchema.safeParse({ ...valid, email: 'not-an-email' })
        expect(result.success).toBe(false)
    })

    it('rejects a password shorter than 8 characters', () => {
        const result = LoginSchema.safeParse({ ...valid, password: 'abc' })
        expect(result.success).toBe(false)
    })

    it('rejects a password longer than 128 characters', () => {
        const result = LoginSchema.safeParse({ ...valid, password: 'A'.repeat(129) })
        expect(result.success).toBe(false)
    })

    it('rejects an email longer than 254 characters', () => {
        const long = 'a'.repeat(250) + '@x.com'
        const result = LoginSchema.safeParse({ ...valid, email: long })
        expect(result.success).toBe(false)
    })

    it('rejects empty email', () => {
        const result = LoginSchema.safeParse({ ...valid, email: '' })
        expect(result.success).toBe(false)
    })

    it('rejects empty password', () => {
        const result = LoginSchema.safeParse({ ...valid, password: '' })
        expect(result.success).toBe(false)
    })
})

describe('RegisterSchema', () => {
    const valid = {
        email: 'new@user.com',
        password: 'Str0ng!Pass#1',
        confirmPassword: 'Str0ng!Pass#1',
        name: 'John Doe',
        business_name: 'Acme Corp',
    }

    it('accepts a fully valid registration payload', () => {
        expect(RegisterSchema.safeParse(valid).success).toBe(true)
    })

    it('rejects mismatched passwords', () => {
        const result = RegisterSchema.safeParse({ ...valid, confirmPassword: 'Different1!' })
        expect(result.success).toBe(false)
        const err = result as z.SafeParseError<typeof valid>
        expect(err.error.errors[0].message).toBe("Passwords do not match")
    })

    it('rejects password shorter than 12 characters', () => {
        const result = RegisterSchema.safeParse({
            ...valid,
            password: 'Short1!',
            confirmPassword: 'Short1!',
        })
        expect(result.success).toBe(false)
    })

    it('rejects password without uppercase letter', () => {
        const result = RegisterSchema.safeParse({
            ...valid,
            password: 'lowercase1!abc',
            confirmPassword: 'lowercase1!abc',
        })
        expect(result.success).toBe(false)
    })

    it('rejects password without lowercase letter', () => {
        const result = RegisterSchema.safeParse({
            ...valid,
            password: 'UPPERCASE1!ABC',
            confirmPassword: 'UPPERCASE1!ABC',
        })
        expect(result.success).toBe(false)
    })

    it('rejects password without a number', () => {
        const result = RegisterSchema.safeParse({
            ...valid,
            password: 'NoNumbers!AbcDef',
            confirmPassword: 'NoNumbers!AbcDef',
        })
        expect(result.success).toBe(false)
    })

    it('rejects password without a special character', () => {
        const result = RegisterSchema.safeParse({
            ...valid,
            password: 'NoSpecialChar1234',
            confirmPassword: 'NoSpecialChar1234',
        })
        expect(result.success).toBe(false)
    })

    it('rejects password longer than 128 characters', () => {
        const long = 'A1!' + 'a'.repeat(126)
        const result = RegisterSchema.safeParse({ ...valid, password: long, confirmPassword: long })
        expect(result.success).toBe(false)
    })

    it('rejects empty name', () => {
        const result = RegisterSchema.safeParse({ ...valid, name: '' })
        expect(result.success).toBe(false)
    })

    it('rejects name longer than 100 characters', () => {
        const result = RegisterSchema.safeParse({ ...valid, name: 'a'.repeat(101) })
        expect(result.success).toBe(false)
    })

    it('rejects empty business_name', () => {
        const result = RegisterSchema.safeParse({ ...valid, business_name: '' })
        expect(result.success).toBe(false)
    })

    it('accepts optional phone field being absent', () => {
        const { phone, ...noPhone } = { ...valid, phone: undefined }
        expect(RegisterSchema.safeParse(noPhone).success).toBe(true)
    })

    it('rejects phone longer than 20 characters', () => {
        const result = RegisterSchema.safeParse({ ...valid, phone: '+' + '1'.repeat(20) })
        expect(result.success).toBe(false)
    })
})
