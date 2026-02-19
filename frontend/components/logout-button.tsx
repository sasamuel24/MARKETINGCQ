"use client";

import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { LogOut } from "lucide-react";

export function LogoutButton() {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleLogout = async () => {
    const supabase = createClient();
    setIsLoading(true);

    await supabase.auth.signOut();
    router.push("/login");
  };

  return (
    <Button
      variant="outline"
      className="w-full bg-transparent"
      onClick={handleLogout}
      disabled={isLoading}
    >
      <LogOut className="mr-2 h-4 w-4" />
      {isLoading ? "Cerrando sesion..." : "Cerrar sesion"}
    </Button>
  );
}
