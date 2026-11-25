import { NavLink, Outlet } from 'react-router-dom';
import { BookOpen, Search } from 'lucide-react';

import { cn } from '../lib/utils';

const NAV_ITEMS = [
  { name: '知识探索', path: '/knowledge', icon: BookOpen, end: true },
  { name: '全文检索', path: '/knowledge/search', icon: Search, end: false },
];

/** Same header/nav treatment as record-app's Topbar so the two apps feel like one product. */
export function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-14 items-center gap-6 px-6">
          <div className="flex items-center gap-2 text-xl font-bold text-primary">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-primary text-primary-foreground">W</div>
            Weakly 知识库
          </div>
          <nav className="flex items-center gap-5 text-sm font-medium text-muted-foreground">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.end}
                className={({ isActive }) =>
                  cn('flex items-center gap-2 transition-colors hover:text-foreground', isActive && 'text-foreground')
                }
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex min-h-0 flex-1">
        <Outlet />
      </main>
    </div>
  );
}
