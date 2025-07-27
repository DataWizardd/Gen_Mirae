import * as React from "react"

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: string;
  storageKey?: string;
}

interface ThemeContextType {
  theme: string;
  setTheme: (theme: string) => void;
}

const ThemeContext = React.createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ 
  children, 
  defaultTheme = "dark", 
  storageKey = "app-theme" 
}: ThemeProviderProps) {
  const [theme, setTheme] = React.useState(defaultTheme);

  React.useEffect(() => {
    const savedTheme = localStorage.getItem(storageKey);
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, [storageKey]);

  const value = React.useMemo(() => ({
    theme,
    setTheme: (newTheme: string) => {
      setTheme(newTheme);
      localStorage.setItem(storageKey, newTheme);
      document.documentElement.setAttribute('data-theme', newTheme);
    }
  }), [theme, storageKey]);

  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => {
  const context = React.useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}; 