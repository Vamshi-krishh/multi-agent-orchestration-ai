"use client";
import { useState } from "react";
import { Layers, Puzzle, ArrowRight, ChevronLeft } from "lucide-react";
import { SERVICES, FEATURES, getComponentRagQuery } from "@/lib/components-data";
import clsx from "clsx";

interface Props {
  onQuery: (question: string, displayText: string) => void;
}

type View = "home" | "components" | "features" | "feature_list";

const COLOR_CLASSES: Record<string, string> = {
  blue:   "bg-blue-500/10   text-blue-400   border-blue-500/20   hover:border-blue-500/50",
  purple: "bg-purple-500/10 text-purple-400 border-purple-500/20 hover:border-purple-500/50",
  green:  "bg-green-500/10  text-green-400  border-green-500/20  hover:border-green-500/50",
  yellow: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20 hover:border-yellow-500/50",
  pink:   "bg-pink-500/10   text-pink-400   border-pink-500/20   hover:border-pink-500/50",
  orange: "bg-orange-500/10 text-orange-400 border-orange-500/20 hover:border-orange-500/50",
  red:    "bg-red-500/10    text-red-400    border-red-500/20    hover:border-red-500/50",
  teal:   "bg-teal-500/10   text-teal-400   border-teal-500/20   hover:border-teal-500/50",
  gray:   "bg-gray-500/10   text-gray-400   border-gray-500/20   hover:border-gray-500/50",
};

export function GreetingCard({ onQuery }: Props) {
  const [view, setView] = useState<View>("home");
  const [selectedService, setSelectedService] = useState<string | null>(null);

  function handleComponentClick(serviceId: string) {
    const svc = SERVICES.find((s) => s.id === serviceId)!;
    onQuery(getComponentRagQuery(serviceId), `Tell me about ${svc.name}`);
  }

  function handleFeatureServiceClick(serviceId: string) {
    const features = FEATURES[serviceId] ?? [];
    if (features.length === 0) {
      const svc = SERVICES.find((s) => s.id === serviceId)!;
      onQuery(
        `What are the main features of ${svc.name} (${svc.fullName})?`,
        `What features does ${svc.name} have?`
      );
      return;
    }
    setSelectedService(serviceId);
    setView("feature_list");
  }

  function handleFeatureClick(ragQuery: string, name: string) {
    onQuery(ragQuery, `Explain: ${name}`);
  }

  // --- Home ---
  if (view === "home") {
    return (
      <div className="space-y-4">
        <p className="text-sm text-gray-300">
          Hi! Hope you're doing great. What would you like to explore today?
        </p>
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => setView("features")}
            className="flex flex-col items-start gap-2 p-4 rounded-xl bg-brand-500/10 border border-brand-500/20 hover:border-brand-500/50 transition-all text-left group"
          >
            <Puzzle className="w-5 h-5 text-brand-500" />
            <span className="text-sm font-medium text-white">Explore Features</span>
            <span className="text-xs text-gray-400">Browse features by service</span>
            <ArrowRight className="w-3.5 h-3.5 text-brand-500 group-hover:translate-x-0.5 transition-transform" />
          </button>

          <button
            onClick={() => setView("components")}
            className="flex flex-col items-start gap-2 p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 hover:border-purple-500/50 transition-all text-left group"
          >
            <Layers className="w-5 h-5 text-purple-400" />
            <span className="text-sm font-medium text-white">Browse Components</span>
            <span className="text-xs text-gray-400">Deep dive into a service</span>
            <ArrowRight className="w-3.5 h-3.5 text-purple-400 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>
    );
  }

  // --- Component list ---
  if (view === "components") {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <button onClick={() => setView("home")} className="text-gray-500 hover:text-gray-300 transition-colors">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <p className="text-sm text-gray-300">Select a component to learn about it:</p>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {SERVICES.map((svc) => (
            <button
              key={svc.id}
              onClick={() => handleComponentClick(svc.id)}
              className={clsx(
                "flex flex-col items-start gap-1 p-3 rounded-xl border transition-all text-left",
                COLOR_CLASSES[svc.color]
              )}
            >
              <span className="text-sm font-semibold">{svc.name}</span>
              <span className="text-[11px] opacity-70 leading-tight">{svc.fullName}</span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  // --- Feature: pick service first ---
  if (view === "features") {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <button onClick={() => setView("home")} className="text-gray-500 hover:text-gray-300 transition-colors">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <p className="text-sm text-gray-300">Which service's features do you want to explore?</p>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {SERVICES.map((svc) => {
            const count = FEATURES[svc.id]?.length ?? 0;
            return (
              <button
                key={svc.id}
                onClick={() => handleFeatureServiceClick(svc.id)}
                className={clsx(
                  "flex flex-col items-start gap-1 p-3 rounded-xl border transition-all text-left",
                  COLOR_CLASSES[svc.color]
                )}
              >
                <span className="text-sm font-semibold">{svc.name}</span>
                <span className="text-[11px] opacity-70">
                  {count > 0 ? `${count} feature${count > 1 ? "s" : ""}` : "Ask RAG"}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  // --- Feature list for selected service ---
  if (view === "feature_list" && selectedService) {
    const svc = SERVICES.find((s) => s.id === selectedService)!;
    const features = FEATURES[selectedService] ?? [];

    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <button onClick={() => setView("features")} className="text-gray-500 hover:text-gray-300 transition-colors">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className={clsx("text-xs font-semibold px-2 py-0.5 rounded", COLOR_CLASSES[svc.color])}>
            {svc.name}
          </span>
          <p className="text-sm text-gray-300">Select a feature:</p>
        </div>
        <div className="space-y-2">
          {features.map((feat) => (
            <button
              key={feat.id}
              onClick={() => handleFeatureClick(feat.ragQuery, feat.name)}
              className="w-full flex items-center justify-between px-4 py-3 rounded-xl bg-[#1e2330] border border-gray-700 hover:border-gray-500 transition-all text-left group"
            >
              <span className="text-sm text-gray-200">{feat.name}</span>
              <ArrowRight className="w-3.5 h-3.5 text-gray-500 group-hover:text-gray-300 group-hover:translate-x-0.5 transition-all" />
            </button>
          ))}
        </div>
      </div>
    );
  }

  return null;
}
