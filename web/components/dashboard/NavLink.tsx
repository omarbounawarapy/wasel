"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface NavLinkProps {
    href: string;
    children: React.ReactNode;
    className?: string;
    activeClassName?: string;
    onClick?: (e: React.MouseEvent) => void;
}

export const NavLink = ({
    href,
    children,
    className,
    activeClassName,
    onClick,
}: NavLinkProps) => {
    const pathname = usePathname();
    const isActive = pathname === href || pathname.startsWith(`${href}/`);

    return (
        <Link prefetch={false}
            href={href}
            onClick={onClick}
            className={cn(className, isActive && activeClassName)}
        >
            {children}
        </Link>
    );
};
