import { MetadataRoute } from 'next'
import { INDEXABLE, SITE_URL } from '@/lib/site'

// output: "export" needs metadata routes to be static.
export const dynamic = 'force-static'

// The demo shows synthetic data under the product name, so crawlers are kept out unless NEXT_PUBLIC_INDEXABLE=1.
export default function robots(): MetadataRoute.Robots {
    if (!INDEXABLE) return { rules: { userAgent: '*', disallow: '/' } }
    return {
        rules: { userAgent: '*', allow: '/', disallow: ['/api', '/dashboard/order'] },
        sitemap: `${SITE_URL}/sitemap.xml`,
    }
}
