import { useState, useEffect } from "react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export function useSystemStatus(setModelStatus: (status: "online" | "offline" | "swapping") => void) {
  const [backendStatus, setBackendStatus] = useState("offline")

  // Health check for API status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        // Check backend status
        const statusResponse = await fetch(`${API_BASE_URL}/api/status`);
        if (statusResponse.ok) {
          setBackendStatus("online");
          
          // Check model status
          try {
            const healthResponse = await fetch(`${API_BASE_URL}/api/health`);
            if (healthResponse.ok) {
              const healthData = await healthResponse.json();
              const aiModelStatus = healthData.dependencies?.ai_model || "error";
              setModelStatus(aiModelStatus === "ok" ? "online" : "offline");
            } else {
              setModelStatus("offline");
            }
          } catch {
            setModelStatus("offline");
          }
        } else {
          setBackendStatus("offline");
          setModelStatus("offline");
        }
      } catch (error) {
        setBackendStatus("offline");
        setModelStatus("offline");
      }
    };
    
    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [setModelStatus]);

  return {
    backendStatus
  }
}
