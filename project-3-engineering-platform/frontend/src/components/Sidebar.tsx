"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, ListTodo, Plus, Cpu } from "lucide-react";
import clsx from "clsx";

const NAV = [
  { href: "/chat", label: "Ask Questions", icon: MessageSquare, badge: "Read Only" },
  { href: "/tasks", label: "Implement Feature", icon: ListTodo },
];

export function Sidebar() {
  const path = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-[#161b27] border-r border-gray-800 flex flex-col z-10">
      {/* Logo — clicking goes back to home (mode selector) */}
      <Link href="/" className="px-5 py-5 border-b border-gray-800 flex items-center gap-2 hover:bg-gray-800/50 transition-colors">
        <Cpu className="w-6 h-6 text-brand-500" />
        <span className="font-bold text-lg text-white">KeyStream</span>
      </Link>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon, badge }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
              path.startsWith(href)
                ? "bg-brand-500/10 text-brand-500 font-medium"
                : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
            )}
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span className="flex-1">{label}</span>
            {badge && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700 text-gray-400">
                {badge}
              </span>
            )}
          </Link>
        ))}
      </nav>

      {/* New Task CTA */}
      <div className="px-3 pb-4">
        <Link
          href="/tasks/new"
          className="flex items-center gap-2 w-full px-3 py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Task
        </Link>
      </div>
    </aside>
  );
}
