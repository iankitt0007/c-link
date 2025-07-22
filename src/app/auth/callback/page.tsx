"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          throw error;
        }

        if (session) {
          // Redirect to dashboard if we have a session
          router.push("/admin/dashboard");
        } else {
          // Redirect to login if we don't have a session
          router.push("/auth/signin");
        }
      } catch (error) {
        console.error("Auth callback error:", error);
        router.push("/auth/signin");
      }
    };

    handleAuthCallback();
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-xl font-semibold mb-2">Processing login...</h2>
        <p className="text-gray-500">Please wait while we complete your authentication.</p>
      </div>
    </div>
  );
}
