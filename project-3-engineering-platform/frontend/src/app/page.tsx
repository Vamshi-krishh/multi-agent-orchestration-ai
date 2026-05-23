import Link from "next/link";
import { MessageSquare, Wrench, ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0f1117] flex flex-col items-center justify-center px-6">
      <div className="max-w-2xl w-full text-center space-y-4 mb-12">
        <h1 className="text-4xl font-bold text-white">KeyStream</h1>
        <p className="text-gray-400 text-lg">
          AI-powered software engineering platform for your microservices codebase
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl w-full">
        {/* Ask Questions — read only */}
        <Link href="/chat" className="group block">
          <div className="h-full bg-[#161b27] border border-gray-800 hover:border-brand-500/50 rounded-2xl p-6 transition-all hover:shadow-lg hover:shadow-brand-500/5">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-500/10 rounded-xl">
                <MessageSquare className="w-6 h-6 text-blue-400" />
              </div>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 font-medium">
                Read Only
              </span>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Ask Questions</h2>
            <p className="text-gray-400 text-sm leading-relaxed">
              Explore your codebase. Understand flows, find classes, explain patterns.
              Never modifies code.
            </p>
            <div className="mt-4 flex items-center gap-1 text-blue-400 text-sm font-medium group-hover:gap-2 transition-all">
              Open chat <ArrowRight className="w-4 h-4" />
            </div>
          </div>
        </Link>

        {/* Implement Feature */}
        <Link href="/tasks" className="group block">
          <div className="h-full bg-[#161b27] border border-gray-800 hover:border-brand-500/50 rounded-2xl p-6 transition-all hover:shadow-lg hover:shadow-brand-500/5">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-brand-500/10 rounded-xl">
                <Wrench className="w-6 h-6 text-brand-500" />
              </div>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 font-medium">
                Implement
              </span>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Implement Feature</h2>
            <p className="text-gray-400 text-sm leading-relaxed">
              Research → Plan → Generate Code → Review → Approve → Apply to codebase.
            </p>
            <div className="mt-4 flex items-center gap-1 text-brand-500 text-sm font-medium group-hover:gap-2 transition-all">
              Implement feature <ArrowRight className="w-4 h-4" />
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}
