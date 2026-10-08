"use client";

import Image from "next/image";
import Link from "next/link";

export default function NotFound() {
    return (
        <main className="min-h-screen w-full flex items-center justify-center bg-surface p-4">
            <div className="max-w-md w-full bg-white rounded-2xl border border-gray-200/70 shadow-sm p-8 text-center space-y-5">
                <Image src="/wasel-logo-compact.png" alt="Wasel" width={180} height={43} className="w-[180px] h-auto mx-auto" />
                <div className="space-y-1">
                    <h1 className="text-xl font-bold text-brand-ink">This page doesn't exist</h1>
                    <p className="text-sm text-gray-600">The link may be old, or the order may have been deleted.</p>
                </div>
                <Link prefetch={false} href="/dashboard"
                      className="inline-flex items-center justify-center px-5 min-h-[44px] rounded-xl bg-brand hover:bg-brand-hover text-white text-sm font-semibold">
                    Back to orders
                </Link>
            </div>
        </main>
    );
}
