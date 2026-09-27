/**
 * Tests for security headers in next.config.mjs and CORS in vercel.json
 *
 * Verifies:
 * - next.config.mjs exports a headers() function
 * - All required security headers are present (X-Frame-Options, CSP, HSTS, etc.)
 * - CSP connect-src is locked down (no wildcard)
 * - vercel.json does not use wildcard '*' for Access-Control-Allow-Origin
 * - vercel.json CORS origin is a specific domain
 * - Pricing.tsx does not contain the ?admin=true bypass
 * - scrolling-logos components import DOMPurify and call sanitize()
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const ROOT = resolve(__dirname, '../..')

function readFile(relative: string): string {
    return readFileSync(resolve(ROOT, relative), 'utf-8')
}

describe('next.config.mjs security headers (C4)', () => {
    const config = readFile('next.config.mjs')

    it('exports a headers() function', () => {
        expect(config).toContain('async headers()')
    })

    it('includes X-Frame-Options header', () => {
        expect(config).toMatch(/X-Frame-Options/)
    })

    it('sets X-Frame-Options to SAMEORIGIN (not DENY which breaks iframes)', () => {
        expect(config).toContain('SAMEORIGIN')
    })

    it('includes X-Content-Type-Options header', () => {
        expect(config).toMatch(/X-Content-Type-Options/)
    })

    it('sets X-Content-Type-Options to nosniff', () => {
        expect(config).toContain('nosniff')
    })

    it('includes Strict-Transport-Security header', () => {
        expect(config).toMatch(/Strict-Transport-Security/)
    })

    it('sets HSTS max-age >= 1 year', () => {
        const match = config.match(/max-age=(\d+)/)
        expect(match).not.toBeNull()
        const maxAge = parseInt(match![1], 10)
        expect(maxAge).toBeGreaterThanOrEqual(31536000)
    })

    it('includes Content-Security-Policy header', () => {
        expect(config).toMatch(/Content-Security-Policy/)
    })

    it('includes Referrer-Policy header', () => {
        expect(config).toMatch(/Referrer-Policy/)
    })

    it('CSP connect-src does not allow all origins (*)', () => {
        const cspLine = config.split('\n').find(l => l.includes('connect-src'))
        if (cspLine) {
            expect(cspLine).not.toContain("'*'")
            expect(cspLine).not.toMatch(/connect-src \*/)
        }
    })

    it('security headers apply to all routes (source "/(.*)")', () => {
        expect(config).toMatch(/source.*\(.*\)/)
    })
})

describe('vercel.json CORS configuration (C5)', () => {
    const vercel = readFile('vercel.json')

    it('does not use wildcard * for Access-Control-Allow-Origin', () => {
        // The value field after Access-Control-Allow-Origin must not be "*"
        const parsed = JSON.parse(vercel)
        const headers = parsed.headers as Array<{ headers: Array<{ key: string; value: string }> }>
        for (const block of headers) {
            for (const h of block.headers) {
                if (h.key === 'Access-Control-Allow-Origin') {
                    expect(h.value).not.toBe('*')
                }
            }
        }
    })

    it('Access-Control-Allow-Origin is a specific https domain', () => {
        const parsed = JSON.parse(vercel)
        const headers = parsed.headers as Array<{ headers: Array<{ key: string; value: string }> }>
        for (const block of headers) {
            for (const h of block.headers) {
                if (h.key === 'Access-Control-Allow-Origin') {
                    expect(h.value).toMatch(/^https?:\/\//)
                }
            }
        }
    })
})

describe('Pricing.tsx admin bypass removal (C3)', () => {
    const pricing = readFile('components/landing/Pricing.tsx')

    it('does not check for ?admin=true query parameter', () => {
        expect(pricing).not.toMatch(/params\.get\(['"]admin['"]\)/)
    })

    it('does not conditionally set isAdmin from URL', () => {
        expect(pricing).not.toMatch(/setIsAdmin\(true\)/)
    })
})

describe('scrolling-logos DOMPurify sanitization (H1)', () => {
    const logos1 = readFile('components/scrolling-logos.tsx')
    const logos2 = readFile('components/ui/scrolling-logos.tsx')

    for (const [name, src] of [['components/scrolling-logos.tsx', logos1], ['components/ui/scrolling-logos.tsx', logos2]]) {
        it(`${name}: imports DOMPurify`, () => {
            expect(src).toMatch(/import DOMPurify/)
        })

        it(`${name}: calls DOMPurify.sanitize() before dangerouslySetInnerHTML`, () => {
            expect(src).toContain('DOMPurify.sanitize(')
        })

        it(`${name}: uses SVG profile in sanitize call`, () => {
            expect(src).toContain('USE_PROFILES')
        })
    }
})
