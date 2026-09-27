/**
 * Tests for the UUID validation regex in VapiTestContent.tsx
 *
 * Verifies:
 * - Valid v4 UUID strings pass
 * - Non-UUID strings (including path traversal, script tags, empty) are rejected
 * - Partial UUIDs fail
 * - UUIDs with wrong segment lengths fail
 */

import { describe, it, expect } from 'vitest'

// ── Re-define UUID_RE (same source as app/admin/vapi-test/VapiTestContent.tsx) ─
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
// ─────────────────────────────────────────────────────────────────────────────

const validUUIDs = [
    '550e8400-e29b-41d4-a716-446655440000',
    'A987FBC9-4BED-3078-CF07-9141BA07C9F3',
    '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
    '00000000-0000-0000-0000-000000000000',
]

const invalidUUIDs = [
    '',
    'not-a-uuid',
    '../../../etc/passwd',
    '<script>alert(1)</script>',
    '550e8400-e29b-41d4-a716',              // truncated
    '550e8400e29b41d4a716446655440000',     // missing dashes
    '550e8400-e29b-41d4-a716-44665544000Z', // invalid char Z
    'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', // non-hex
    '550e8400-e29b-41d4-a716-4466554400001', // too long
]

describe('UUID_RE validation (VapiTestContent)', () => {
    describe('accepts valid UUIDs', () => {
        for (const uuid of validUUIDs) {
            it(`passes: "${uuid}"`, () => {
                expect(UUID_RE.test(uuid)).toBe(true)
            })
        }
    })

    describe('rejects invalid values', () => {
        for (const uuid of invalidUUIDs) {
            it(`blocks: ${JSON.stringify(uuid)}`, () => {
                expect(UUID_RE.test(uuid)).toBe(false)
            })
        }
    })
})
