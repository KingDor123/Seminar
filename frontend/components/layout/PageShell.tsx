import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface PageShellProps {
  children: ReactNode;
  className?: string;
}

export function PageShell({ children, className }: PageShellProps) {
  return (
    <div className={cn("min-h-screen bg-background pb-24 pt-6 md:pb-6 md:pt-24", className)}>
      {children}
    </div>
  );
}
