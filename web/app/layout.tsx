import type React from "react"
import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import "./globals.css"

export const metadata: Metadata = {
  metadataBase: new URL("http://localhost:5173"),
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
    <html lang="en">
      <head>
        <style>{`
html {
  font-family: ${GeistSans.style.fontFamily};
  --font-sans: ${GeistSans.variable};
  --font-mono: ${GeistMono.variable};
}
        `}</style>
      </head>
      <body suppressHydrationWarning>
        {children}
      </body>
    </html>
  )
}

