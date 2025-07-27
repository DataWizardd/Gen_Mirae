import { ThemeToggle } from './ThemeToggle';
import { BarChart3, Bell } from 'lucide-react';
import { Button } from './ui/button';

interface MobileHeaderProps {
  title: string;
}

export function MobileHeader({ title }: MobileHeaderProps) {
  const isLongTitle = title.length > 10;
  
  return (
    <header className="sticky top-0 z-40 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60 border-b">
      <div className="flex items-center justify-between px-4 py-3 safe-area-inset-top">
        <div className="flex items-center space-x-3 flex-1 min-w-0">
          <div className="flex items-center space-x-2 min-w-0">
            <BarChart3 className="w-6 h-6 text-primary flex-shrink-0" />
            <h1 className={`font-medium truncate ${isLongTitle ? 'text-sm' : 'text-lg'}`}>
              {title}
            </h1>
          </div>
        </div>
        
        <div className="flex items-center space-x-2 flex-shrink-0">
          <Button variant="ghost" size="sm" className="h-9 w-9 p-0">
            <Bell className="w-4 h-4" />
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}