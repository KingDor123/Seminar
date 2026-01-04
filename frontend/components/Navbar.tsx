'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { useState } from 'react';
import { BarChart3, Home, LogIn, UserCircle, UserPlus, type LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { he } from '../constants/he';

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  mobileOnly?: boolean;
};

const signedInNav: NavItem[] = [
  { href: '/home', label: he.nav.home, icon: Home },
  { href: '/sessions', label: he.nav.sessions, icon: BarChart3 },
  { href: '/profile', label: he.nav.profile, icon: UserCircle, mobileOnly: true },
];

const signedOutNav: NavItem[] = [
  { href: '/login', label: he.nav.signIn, icon: LogIn },
  { href: '/register', label: he.nav.signUp, icon: UserPlus },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const navItems = user ? signedInNav : signedOutNav;

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-card/95 backdrop-blur-sm md:top-0 md:bottom-auto md:border-b md:border-t-0">
      <div className="container mx-auto flex items-center justify-between gap-2 px-4 py-3 md:py-4">
        <div className="hidden items-center gap-3 md:flex">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <span className="text-sm font-heading font-semibold">{he.app.shortName}</span>
          </div>
          <span className="text-xl font-heading font-semibold text-foreground">{he.app.name}</span>
        </div>

        <div className="flex flex-1 items-center justify-center gap-2 md:flex-none">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex flex-col items-center gap-1 rounded-xl px-5 py-2.5 transition-all duration-200 md:flex-row md:gap-2 md:px-4",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  item.mobileOnly ? "md:hidden" : "",
                )}
              >
                <Icon className="h-5 w-5" />
                <span className="text-xs font-medium md:text-sm">{item.label}</span>
              </Link>
            );
          })}
        </div>

        <div className="hidden w-40 items-center justify-end md:flex">
          {user && (
            <div className="relative">
              <button
                onClick={() => setIsProfileOpen((prev) => !prev)}
                className="flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 text-sm text-muted-foreground transition hover:text-foreground"
                id="user-menu-button"
                aria-expanded={isProfileOpen}
                aria-haspopup="true"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-semibold">
                  {user.full_name?.charAt(0).toUpperCase() || he.nav.accountInitial}
                </div>
                <span className="font-medium">{user.full_name?.split(' ')[0] || he.nav.account}</span>
              </button>

              {isProfileOpen && (
                <div
                  className="absolute right-0 mt-2 w-56 rounded-xl border border-border bg-card p-2 shadow-lg"
                  role="menu"
                  aria-orientation="vertical"
                  aria-labelledby="user-menu-button"
                  onMouseLeave={() => setIsProfileOpen(false)}
                >
                  <div className="px-3 py-2 text-xs text-muted-foreground border-b border-border">
                    {he.nav.signedInAs}
                    <div className="truncate font-medium text-foreground">{user.email}</div>
                  </div>
                  <Link
                    href="/profile"
                    className="block rounded-lg px-3 py-2 text-sm text-foreground hover:bg-muted"
                    role="menuitem"
                  >
                    {he.nav.yourProfile}
                  </Link>
                  <button
                    onClick={logout}
                    className="block w-full rounded-lg px-3 py-2 text-left text-sm text-destructive hover:bg-muted"
                    role="menuitem"
                  >
                    {he.nav.signOut}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
