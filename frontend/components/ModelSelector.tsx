import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Check, ChevronDown, Cpu, FileText, Layers, Info } from "lucide-react"

interface ModelInfo {
  name: string
  display_name: string
  type: string
  description?: string
}

interface InferenceMode {
  display_name: string
  description: string
  hover_text?: string
  models: Record<string, ModelInfo>
}

interface AvailableModels {
  inference_modes: Record<string, InferenceMode>
}

interface CurrentModel {
  current_model: string
  inference_mode: string
  status: string
}

interface ModelSelectorProps {
  availableModels: AvailableModels | null
  currentModel: CurrentModel | null
  isSwappingModel: boolean
  onModelSwap: (modelName: string, inferenceMode: string) => void
}

export function ModelSelector({ availableModels, currentModel, isSwappingModel, onModelSwap }: ModelSelectorProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline" 
          size="sm" 
          className="flex items-center space-x-2 bg-transparent"
          disabled={isSwappingModel}
        >
          <Cpu className="h-4 w-4" />
          <span>{currentModel?.status === "swapping" ? "Switching Model..." : 
                availableModels?.inference_modes?.[currentModel?.inference_mode]?.display_name || "Model"}</span>
          <ChevronDown className="h-3 w-3" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        {availableModels?.inference_modes && Object.entries(availableModels.inference_modes).map(([modeKey, mode]: [string, any]) => (
          <div key={modeKey}>
            <div className="px-2 py-1.5 text-sm font-semibold text-gray-700 flex items-center">
              {modeKey === "one_shot" ? <FileText className="h-4 w-4 mr-2" /> : <Layers className="h-4 w-4 mr-2" />}
              {mode.display_name}
              {mode.hover_text && (
                <div className="ml-1" title={mode.hover_text}>
                  <Info className="h-3 w-3 text-gray-400 hover:text-gray-600 cursor-help" />
                </div>
              )}
            </div>
            {Object.entries(mode.models || {}).map(([modelName, modelInfo]: [string, any]) => (
              <DropdownMenuItem
                key={modelName}
                onClick={() => onModelSwap(modelName, modeKey)}
                className="flex items-center justify-between pl-6"
                disabled={isSwappingModel}
                title={modelInfo.description || modelInfo.display_name}
              >
                <div className="flex items-center">
                  <span className="text-sm">{modelInfo.display_name}</span>
                  {modelInfo.description && modelInfo.type === "hybrid_combination" && (
                    <div className="ml-1" title={modelInfo.description}>
                      <Info className="h-3 w-3 text-gray-400 hover:text-gray-600 cursor-help" />
                    </div>
                  )}
                </div>
                {currentModel?.current_model === modelName && currentModel?.inference_mode === modeKey && (
                  <Check className="h-4 w-4 text-green-600" />
                )}
              </DropdownMenuItem>
            ))}
            {Object.keys(mode.models || {}).length === 0 && (
              <div className="px-6 py-2 text-xs text-gray-500">Coming Soon</div>
            )}
          </div>
        ))}
        {!availableModels?.inference_modes && (
          <div className="px-2 py-2 text-sm text-gray-500">Loading models...</div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
