import { 
  Home, 
  Newspaper, 
  FileText, // Add FileText icon for the report
  BrainCircuit,
  MessageCircle 
} from 'lucide-react';
// import { cn } from "./ui/utils"; // Not used

interface BottomNavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const navItems = [
  { id: 'dashboard', label: '홈', icon: Home },
  { id: 'feed', label: '투자 피드', icon: Newspaper },
  { id: 'report', label: 'AI 리포트', icon: FileText },
  { id: 'discovery', label: 'AI 종목 발굴', icon: BrainCircuit },
  { id: 'chat', label: 'AI Analyst', icon: MessageCircle },
];

export function BottomNavigation({ activeTab, onTabChange }: BottomNavigationProps) {
  return (
    <div className="absolute bottom-0 left-0 right-0 bg-card/95 backdrop-blur border-t z-40">
      <div className="flex justify-around items-center h-16">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`flex flex-col items-center justify-center py-2 px-3 rounded-lg min-h-[60px] transition-colors ${
                isActive 
                  ? 'text-primary bg-primary/10' 
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className={`w-5 h-5 mb-1 ${isActive ? 'text-primary' : ''}`} />
              <span className="text-xs" style={{ fontSize: '11px' }}>{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}