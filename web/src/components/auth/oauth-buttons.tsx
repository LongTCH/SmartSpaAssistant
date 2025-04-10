"use client"

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { authService } from '@/services/api/auth.service';

export default function OAuthButtons() {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  const handleGoogleLogin = async () => {
    setIsLoading(true);
    window.location.href = authService.getGoogleAuthUrl();
  };
  
  return (
    <div className="flex flex-col space-y-2">
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>
      
      <Button 
        variant="outline" 
        type="button" 
        disabled={isLoading}
        className="flex items-center justify-center gap-2"
        onClick={handleGoogleLogin}
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          viewBox="0 0 488 512" 
          className="h-4 w-4"
          fill="currentColor"
        >
          <path d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 24.9 3.9 41.4z"/>
        </svg>
        {isLoading ? "Connecting..." : "Sign in with Google"}
      </Button>
    </div>
  );
}
