import type React from "react"
import type { Metadata, Viewport } from "next"
import { GeistSans } from "geist/font/sans"
import "./globals.css"
import AccessGate from "@/components/AccessGate"
import ServiceWorker from "@/components/ServiceWorker"
import { LangProvider } from "@/lib/i18n"
import { INDEXABLE, SITE_DESCRIPTION, SITE_TITLE, SITE_URL } from "@/lib/site"

export const metadata: Metadata = {
  // The public origin comes from NEXT_PUBLIC_SITE_URL (lib/site.ts); a production build fails without it.
  metadataBase: new URL(SITE_URL),
  title: SITE_TITLE,
  description: SITE_DESCRIPTION,
  applicationName: "Wasel",
  alternates: { canonical: "/" },
  robots: INDEXABLE ? undefined : { index: false, follow: false },
  openGraph: {
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    url: "/",
    siteName: "Wasel",
    type: "website",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "Wasel: High 87 before the customer's reply, Low 16 after" }],
  },
  twitter: { card: "summary_large_image", title: SITE_TITLE, description: SITE_DESCRIPTION, images: ["/og-image.png"] },
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/icon-16.png", sizes: "16x16", type: "image/png" },
      { url: "/icon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
  manifest: "/site.webmanifest",
}

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f6f5f1" },
    { media: "(prefers-color-scheme: dark)", color: "#111214" },
  ],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" dir="ltr" className={GeistSans.variable}>
      <body suppressHydrationWarning>
        <LangProvider>
          {children}
          <AccessGate />
        </LangProvider>
        <ServiceWorker />
      </body>
    </html>
  )
}
