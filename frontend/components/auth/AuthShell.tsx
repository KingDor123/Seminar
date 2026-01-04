import { ReactNode } from "react";
import { PageShell } from "@/components/layout/PageShell";

interface AuthShellProps {
  title: string;
  subtitle?: ReactNode;
  children: ReactNode;
}

export function AuthShell({ title, subtitle, children }: AuthShellProps) {
  return (
    <PageShell className="flex items-center justify-center">
      <div className="w-full max-w-md px-4">
        <div className="rounded-2xl border border-border bg-card p-8 shadow-sm">
          <div className="text-center">
            <h2 className="text-3xl font-heading font-bold text-foreground">{title}</h2>
            {subtitle && <div className="mt-2 text-sm text-muted-foreground">{subtitle}</div>}
          </div>
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </PageShell>
  );
}
