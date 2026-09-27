import { MetadataRoute } from 'next'

// output: "export" needs metadata routes to be static.
export const dynamic = 'force-static'

export default function robots(): MetadataRoute.Robots {
    return {
        rules: { userAgent: '*', allow: '/', disallow: ['/api'] },
    }
}
