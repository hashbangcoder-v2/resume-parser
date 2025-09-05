import { useState, useEffect } from "react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export function useModels() {
  const [availableModels, setAvailableModels] = useState<any>(null)
  const [currentModel, setCurrentModel] = useState<any>(null)
  const [modelStatus, setModelStatus] = useState<"online" | "offline" | "swapping">("offline")
  const [isSwappingModel, setIsSwappingModel] = useState(false)

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/models/available`);
        if (response.ok) {
          const data = await response.json();
          setAvailableModels(data);
        } else {
          console.warn("Models API not available yet");
          setAvailableModels({ inference_modes: {} });
        }
        
        // Get current model status
        const statusResponse = await fetch(`${API_BASE_URL}/api/models/status`);
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setCurrentModel(statusData);
          
          // Update model status based on response
          if (statusData.status === "swapping") {
            setModelStatus("swapping");
          } else if (statusData.status === "idle" && statusData.current_model) {
            setModelStatus("online");
          } else {
            setModelStatus("offline");
          }
        } else {
          setModelStatus("offline");
        }
      } catch (error) {
        console.error("Failed to fetch models:", error);        
        setAvailableModels({ inference_modes: {} });
      }
    };
    fetchModels();
  }, []);

  const handleModelSwap = async (modelName: string, inferenceMode: string) => {
    setIsSwappingModel(true);
    
    // Store previous model for fallback
    const previousModel = currentModel;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/models/swap`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_name: modelName,
          inference_mode: inferenceMode,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log("Model swap initiated:", result);
      
      // Update current model to show switching status
      setCurrentModel({
        current_model: modelName,
        inference_mode: inferenceMode,
        status: "swapping"
      });
      setModelStatus("swapping");
            
      // TODO: Make this more robust
      let pollAttempts = 0;
      const maxPollAttempts = 50; // 50 attempts * 3 seconds = 150 seconds max
      
      const pollStatus = async () => {
        try {
          const statusResponse = await fetch(`${API_BASE_URL}/api/models/status`);
          const statusData = await statusResponse.json();
          
          if (statusData.status === "idle" && statusData.current_model === modelName) {
            // Success - model loaded
            setCurrentModel(statusData);
            setModelStatus("online");
            setIsSwappingModel(false);
            console.log("Model swap completed successfully");
          } else if (statusData.status === "error" || pollAttempts >= maxPollAttempts) {
            // Failed or timeout - fallback to default model
            console.error("Model swap failed, falling back to default model");
            await fallbackToDefaultModel(previousModel);
          } else {
            // Still swapping, continue polling
            pollAttempts++;
            setTimeout(pollStatus, 3000);
          }
        } catch (error) {
          console.error("Failed to poll model status:", error);
          if (pollAttempts >= maxPollAttempts) {
            await fallbackToDefaultModel(previousModel);
          } else {
            pollAttempts++;
            setTimeout(pollStatus, 3000);
          }
        }
      };
      
      // Start polling after initial delay
      setTimeout(pollStatus, 3000);
      
    } catch (error) {
      console.error("Failed to initiate model swap:", error);
      alert("Failed to switch model. Please try again.");
      await fallbackToDefaultModel(previousModel);
    }
  };

  const fallbackToDefaultModel = async (previousModel: any) => {
    try {
      // Try to swap back to default model
      const defaultModel = "Qwen/Qwen2.5-Omni-7B"; // Default from config
      const response = await fetch(`${API_BASE_URL}/api/models/swap`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_name: defaultModel,
          inference_mode: "one_shot",
        }),
      });

      if (response.ok) {
        console.log("Fallback to default model initiated");
        setCurrentModel({
          current_model: defaultModel,
          inference_mode: "one_shot",
          status: "swapping"
        });
        
        // Poll for default model completion
        setTimeout(async () => {
          try {
            const statusResponse = await fetch(`${API_BASE_URL}/api/models/status`);
            const statusData = await statusResponse.json();
            setCurrentModel(statusData);
          } catch (error) {
            console.error("Failed to get status after fallback:", error);
            // Restore previous model as last resort
            setCurrentModel(previousModel);
          }
          setIsSwappingModel(false);
        }, 10000);
      } else {
        throw new Error("Fallback failed");
      }
    } catch (error) {
      console.error("Fallback to default model failed:", error);
      setCurrentModel(previousModel || { current_model: null, status: "error" });
      setIsSwappingModel(false);
      alert("Model switch failed. Please check the model service.");
    }
  };

  return {
    availableModels,
    currentModel,
    modelStatus,
    isSwappingModel,
    handleModelSwap,
    setModelStatus
  }
}
