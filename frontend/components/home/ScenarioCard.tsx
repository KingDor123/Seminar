import { Check, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface ScenarioCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  variant: "calm" | "support" | "social" | "focus";
  selected?: boolean;
  onSelect?: () => void;
  delay?: number;
}

const variantStyles = {
  calm: {
    bg: "bg-calm-soft",
    icon: "bg-calm/10 text-calm",
    border: "border-calm/20",
    hover: "hover:border-calm/40 hover:shadow-calm/10",
  },
  support: {
    bg: "bg-support-soft",
    icon: "bg-support/10 text-support",
    border: "border-support/20",
    hover: "hover:border-support/40 hover:shadow-support/10",
  },
  social: {
    bg: "bg-social-soft",
    icon: "bg-social/10 text-social",
    border: "border-social/20",
    hover: "hover:border-social/40 hover:shadow-social/10",
  },
  focus: {
    bg: "bg-focus-soft",
    icon: "bg-focus/10 text-focus",
    border: "border-focus/20",
    hover: "hover:border-focus/40 hover:shadow-focus/10",
  },
};

export function ScenarioCard({
  title,
  description,
  icon: Icon,
  variant,
  selected = false,
  onSelect,
  delay = 0,
}: ScenarioCardProps) {
  const styles = variantStyles[variant];

  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "group text-left rounded-2xl border-2 p-6 transition-all duration-300 hover-lift animate-fade-in",
        styles.bg,
        styles.border,
        styles.hover,
        "hover:shadow-xl",
        selected ? "ring-2 ring-primary/40" : "",
      )}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start gap-4">
        <div
          className={cn(
            "flex h-14 w-14 shrink-0 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110",
            styles.icon,
          )}
        >
          <Icon className="h-7 w-7" />
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-lg font-heading font-semibold text-foreground">{title}</h3>
            <span
              className={cn(
                "inline-flex h-5 w-5 items-center justify-center rounded-full border",
                selected ? "border-primary bg-primary text-primary-foreground" : "border-border text-muted-foreground",
              )}
            >
              {selected && <Check className="h-3 w-3" />}
            </span>
          </div>
          <p className="text-sm leading-relaxed text-muted-foreground">{description}</p>
        </div>
      </div>
    </button>
  );
}
