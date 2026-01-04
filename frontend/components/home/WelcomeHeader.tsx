import { Leaf } from "lucide-react";
import { he } from "../../constants/he";

interface WelcomeHeaderProps {
  name?: string;
}

export function WelcomeHeader({ name }: WelcomeHeaderProps) {
  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? he.welcome.morning : hour < 17 ? he.welcome.afternoon : he.welcome.evening;

  return (
    <div className="mb-8 animate-fade-in text-center md:text-left">
      <div className="mb-3 flex items-center justify-center gap-2 md:justify-start">
        <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <Leaf className="h-5 w-5" />
        </span>
        <span className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
          {he.app.name}
        </span>
      </div>
      <h1 className="mb-3 text-3xl font-heading font-bold text-foreground md:text-4xl">
        {greeting}
        {name ? `, ${name}` : ""}
      </h1>
      <p className="text-lg text-muted-foreground">
        {he.welcome.prompt}
      </p>
    </div>
  );
}
