"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Cpu } from "lucide-react";
import clsx from "clsx";

const TABS = [
  { href: "/chat",  label: "Ask Questions" },
  { href: "/tasks", label: "Implement Feature" },
];

export function TopBar() {
  const path = usePathname();

  return (
    <header className="h-12 shrink-0 bg-[#0f1117] border-b border-gray-800 flex items-center px-4 gap-6 z-20">
      {/* Logo */}
      <Link href="/" className="flex items-center gap-2 shrink-0">
        <Cpu className="w-4 h-4 text-brand-500" />
        <span className="font-bold text-sm text-white">KeyStream</span>
      </Link>

      {/* Tabs — center */}
      <div className="flex-1 flex items-center justify-center">
        <div className="flex items-center gap-1 bg-gray-800/60 rounded-lg p-1">
          {TABS.map(({ href, label }) => {
            const active = path.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
                  active
                    ? "bg-brand-500 text-white shadow"
                    : "text-gray-400 hover:text-gray-200"
                )}
              >
                {label}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Right spacer — keeps tabs centered */}
      <div className="w-24 shrink-0" />
    </header>
  );
}
