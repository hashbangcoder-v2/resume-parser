import { Button } from "@/components/ui/button"
import { Upload, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"
import { SystemStatus } from "./SystemStatus"

interface ControlButtonsProps {
  isUploading: boolean
  isRefreshing: boolean
  modelStatus: string
  currentModel: any
  backendStatus: string
  lastUpdated: string
  isClient: boolean
  onFileUpload: () => void
  onRefresh: () => void
}

export function ControlButtons({
  isUploading,
  isRefreshing,
  modelStatus,
  currentModel,
  backendStatus,
  lastUpdated,
  isClient,
  onFileUpload,
  onRefresh
}: ControlButtonsProps) {
  return (
    <div className="flex flex-col items-end space-y-3">
      <div className="flex items-center space-x-4">
        <Button 
          onClick={onFileUpload} 
          disabled={isUploading || modelStatus === "offline" || currentModel?.status === "swapping"} 
          className="flex items-center space-x-2"
        >
          <Upload className={cn("h-4 w-4", isUploading && "animate-pulse")} />
          <span>{isUploading ? "Uploading..." : "Upload Resumes"}</span>
        </Button>
        <Button variant="outline" onClick={onRefresh} className="flex items-center space-x-2 bg-transparent">
          <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin-slow")} />
          <span>Refresh</span>
        </Button>
        <SystemStatus 
          backendStatus={backendStatus}
          modelStatus={modelStatus}
          isUploading={isUploading}
          isRefreshing={isRefreshing}
        />
      </div>
      {isClient && <div className="text-sm text-gray-500">Last Updated: {lastUpdated}</div>}
    </div>
  )
}
