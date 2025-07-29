import { ThemeToggle } from './ThemeToggle';
// import { BarChart3, Bell } from 'lucide-react';
import { Button } from './ui/button';

interface MobileHeaderProps {
  // title: string; // The title is now hardcoded
}

export function MobileHeader({}: MobileHeaderProps) {
  return (
    <header className="sticky top-0 z-40 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60 border-b border-border">
      <div className="flex items-center justify-between px-4 h-20">
        <div className="flex items-center">
          {/* <BarChart3 className="w-6 h-6 text-primary" /> */}
          <h1 className="font-semibold text-2xl truncate">
            <span style={{ color: '#0055A5' }}>MIRAE ASSET</span>
            <span style={{ color: '#F37021' }}> AI PORTAL</span>
          </h1>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* <Button variant="ghost" size="sm" className="h-9 w-9 p-0 text-card-foreground hover:text-primary">
            <Bell className="w-5 h-5" />
          </Button> */}
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}