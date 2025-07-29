// import { Button } from "./ui/button";
// import { CircleUser, Bell, Search, Settings } from "lucide-react";
// import { Input } from "./ui/input";
import { ThemeToggle } from "./ThemeToggle"; // ThemeToggle import

export function DesktopHeader() {
  return (
    <div className="hidden md:flex items-center justify-between space-y-2 mb-6 pb-4 border-b">
      <h2 className="text-xl font-bold tracking-tight">
        <span style={{ color: '#0055A5' }}> MIRAE ASSET</span>
        <span style={{ color: '#F37021' }}> AI PORTAL</span>
      </h2>
      <div className="flex items-center space-x-2">
        <ThemeToggle />
      </div>
    </div>
  );
} 