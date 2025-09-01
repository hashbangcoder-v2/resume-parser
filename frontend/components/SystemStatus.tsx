import { cn } from "@/lib/utils"

interface SystemStatusProps {
  backendStatus: string
  modelStatus: string
  isUploading: boolean
  isRefreshing: boolean
}

export function SystemStatus({ backendStatus, modelStatus, isUploading, isRefreshing }: SystemStatusProps) {
  const getSystemStatusColor = () => {
    if (modelStatus === "swapping") {
      return "bg-orange-500"; // Model swapping - orange
    } else if (backendStatus === "online" && modelStatus === "online") {
      return "bg-green-500"; // Both online - green
    } else if (backendStatus === "online" && modelStatus === "offline") {
      return "bg-orange-500"; // Model offline - orange
    } else if (backendStatus === "offline") {
      return "bg-red-500"; // Backend offline - red
    } else {
      return "bg-yellow-500"; // Mixed state - yellow
    }
  };

  const getSystemStatusText = () => {
    if (modelStatus === "swapping") {
      return "Switching Model...";
    } else if (backendStatus === "online" && modelStatus === "online") {
      return "System Online";
    } else if (backendStatus === "online" && modelStatus === "offline") {
      return "AI Model Offline";
    } else if (backendStatus === "offline" && modelStatus === "online") {
      return "Backend Offline";
    } else {
      return "System Offline";
    }
  };

  const getSystemStatusAnimation = () => {
    if (modelStatus === "swapping" || isUploading || isRefreshing) {
      return "animate-pulse";
    } else {
      return "";
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <div 
        className={cn("w-3 h-3 rounded-full", getSystemStatusColor(), getSystemStatusAnimation())} 
        title={getSystemStatusText()}
      />
      <span 
        className="text-sm text-gray-600 cursor-help" 
        title={getSystemStatusText()}
      >
        {getSystemStatusText()}
      </span>
    </div>
  )
}
