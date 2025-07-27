import { Button } from './ui/button';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from './ui/use-theme';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleTheme}
      className="h-8 w-8 px-0"
    >
      {theme === 'light' ? (
        <Moon className="h-4 w-4" />
      ) : (
        <Sun className="h-4 w-4" />
      )}
      <span className="sr-only">
        {theme === 'light' ? '다크모드로 전환' : '라이트모드로 전환'}
      </span>
    </Button>
  );
}