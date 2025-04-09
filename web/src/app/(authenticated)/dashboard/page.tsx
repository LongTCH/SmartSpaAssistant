import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  return (
    <div className="flex-1 p-8">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-card p-6 rounded-lg border">
          <h2 className="text-xl font-semibold mb-2">Welcome Back</h2>
          <p className="text-muted-foreground">
            This is your personal dashboard where you can manage your profile and settings.
          </p>
        </div>
        
        <div className="bg-card p-6 rounded-lg border">
          <h2 className="text-xl font-semibold mb-2">Activity</h2>
          <p className="text-muted-foreground">
            Track your recent activity and interactions with the platform.
          </p>
        </div>
        
        <div className="bg-card p-6 rounded-lg border">
          <h2 className="text-xl font-semibold mb-2">Resources</h2>
          <p className="text-muted-foreground">
            Access valuable resources and materials tailored for DUT graduates.
          </p>
        </div>
      </div>
    </div>
  );
}
