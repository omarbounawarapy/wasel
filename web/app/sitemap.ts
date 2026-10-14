import { MetadataRoute } from 'next'
import { PAGES, SITE_URL } from '@/lib/site'

export const dynamic = 'force-static'

// Real routes only. /dashboard/order needs an ?id= and shows one order, so it stays out.
export default function sitemap(): MetadataRoute.Sitemap {
    return Object.keys(PAGES)
        .filter(p => p !== '/dashboard/order')
        .map(p => ({ url: p === '/' ? `${SITE_URL}/` : `${SITE_URL}${p}/` }))
}
