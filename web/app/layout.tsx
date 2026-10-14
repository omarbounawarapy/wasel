import type React from "react"
import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import "./globals.css"
import AccessGate from "@/components/AccessGate"

export const metadata: Metadata = {
  // NEXT_PUBLIC_SITE_URL: the public origin, set at build time for a deployed site; the fallback is `npm run dev`
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:5173"),
  title: "Wasel · COD order risk",
  description: "Wasel reads what your cash-on-delivery customers write, scores the refusal risk and drafts the confirmation message.",
  icons: {
    icon: [{ url: "/favicon.ico", sizes: "any" }, { url: "/wasel-mark.png", type: "image/png" }],
    apple: "/apple-touch-icon.png",
  },
  manifest: "/site.webmanifest",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body suppressHydrationWarning>
        {children}
        <AccessGate />
      </body>
    </html>
  )
}

