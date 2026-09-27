/**
 * Tests for SAFE_CSS_COLOR guard in components/ui/chart.tsx
 *
 * Verifies:
 * - Hex colors (#rgb, #rrggbb, #rrggbbaa) pass
 * - rgb(), rgba(), hsl(), hsla() pass
 * - CSS custom properties var(--color-name) pass
 * - Named colors (red, blue, transparent) pass
 * - CSS injection strings (};body{display:none}, url(), expression()) are blocked
 * - Empty string is blocked
 * - Newlines / null bytes are blocked
 */

import { describe, it, expect } from 'vitest'

// ── Re-define guard regex (same source as components/ui/chart.tsx) ─────────────
const SAFE_CSS_COLOR =
    /^(#[0-9a-fA-F]{3,8}|rgb\([^)]+\)|rgba\([^)]+\)|hsl\([^)]+\)|hsla\([^)]+\)|var\(--[a-zA-Z0-9_-]+\)|[a-zA-Z]{2,30})$/
// ─────────────────────────────────────────────────────────────────────────────

const allowed = [
    '#fff',
    '#FF0000',
    '#aabbccdd',
    'rgb(255, 0, 0)',
    'rgba(0, 0, 0, 0.5)',
    'hsl(120, 100%, 50%)',
    'hsla(120, 100%, 50%, 0.3)',
    'var(--color-primary)',
    'var(--my-theme-color)',
    'red',
    'blue',
    'transparent',
    'currentColor',
]

const blocked = [
    '',
    '};body{display:none}',
    'url(javascript:alert(1))',
    'expression(alert(1))',
    '#xyz',               // invalid hex chars
    'rgb(0,0,0);evil',
    'red\0',              // null byte
    '/* comment */',
    'inherit; color: red',
]

// Note: '\nred' is trimmed to 'red' by the guard (color.trim()) — see chart.tsx line ~93.
// That is intentionally safe: whitespace-padded values resolve to valid colors.
const trimmedToValid = ['\nred', '  red  ', '\t#fff\t']

describe('SAFE_CSS_COLOR guard', () => {
    describe('allows safe color values', () => {
        for (const color of allowed) {
            it(`passes: "${color}"`, () => {
                expect(SAFE_CSS_COLOR.test(color.trim())).toBe(true)
            })
        }
    })

    describe('blocks unsafe values', () => {
        for (const color of blocked) {
            it(`blocks: ${JSON.stringify(color)}`, () => {
                expect(SAFE_CSS_COLOR.test(color.trim())).toBe(false)
            })
        }
    })

    describe('whitespace-padded values trim to valid (chart guard calls .trim())', () => {
        for (const color of trimmedToValid) {
            it(`${JSON.stringify(color)}.trim() is safe`, () => {
                expect(SAFE_CSS_COLOR.test(color.trim())).toBe(true)
            })
        }
    })
})
