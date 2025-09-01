"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import {
  Upload,
  RefreshCw,
  Check,
  ChevronDown,
  CheckCircle,
  XCircle,
  AlertCircle,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ExternalLink,
  User,
  Plus,
  FileText,
  Cpu,
  Layers,
  Info,
} from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

const getStatusIcon = (status: string) => {
  switch (status) {
    case "Shortlisted":
      return <CheckCircle className="h-4 w-4 text-green-600" />
    case "Rejected":
      return <XCircle className="h-4 w-4 text-red-600" />
    case "Needs Review":
      return <AlertCircle className="h-4 w-4 text-yellow-600" />
    default:
      return null
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case "Shortlisted":
      return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">{status}</Badge>
    case "Rejected":
      return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">{status}</Badge>
    case "Needs Review":
      return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">{status}</Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

export default function CandidateDashboard() {
  const [selectedJob, setSelectedJob] = useState<any>(null)
  const [jobs, setJobs] = useState<any[]>([])
  const [open, setOpen] = useState(false)
  const [backendStatus, setBackendStatus] = useState("offline")

  const [lastUpdated, setLastUpdated] = useState(new Date().toLocaleString())
  const [candidates, setCandidates] = useState<any[]>([])
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc")
  const [userInfo, setUserInfo] = useState({ name: "", email: "" })
  const [isClient, setIsClient] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [showCreateJobModal, setShowCreateJobModal] = useState(false)
  const [newJobTitle, setNewJobTitle] = useState("")
  const [newJobDescription, setNewJobDescription] = useState("")
  const [isCreatingJob, setIsCreatingJob] = useState(false)
  const [showJobDescriptionModal, setShowJobDescriptionModal] = useState(false)
  const [editingJobDescription, setEditingJobDescription] = useState("")
  const [isUpdatingJob, setIsUpdatingJob] = useState(false)
  const [availableModels, setAvailableModels] = useState<any>(null)
  const [currentModel, setCurrentModel] = useState<any>(null)
  const [modelStatus, setModelStatus] = useState<"online" | "offline" | "swapping">("offline")
  const [isSwappingModel, setIsSwappingModel] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])
  
  // Fetch Jobs 
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/jobs`);
        const data = await response.json();
        setJobs(data);
      } catch (error) {
        console.error("Failed to fetch jobs:", error);
        console.error("API_BASE_URL:", API_BASE_URL);
      }
    };
    fetchJobs();
  }, []);
  
  // Fetch user info
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/user`);
        const data = await response.json();
        setUserInfo(data);
      } catch (error) {
        console.error("Failed to fetch user info:", error);
      }
    };
    fetchUser();
  }, []);

  // Fetch available models
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
        // Set empty state to prevent undefined errors
        setAvailableModels({ inference_modes: {} });
      }
    };
    fetchModels();
  }, []);
  
  // Fetch candidates when a job is selected
  useEffect(() => {
    if (selectedJob) {
      const fetchCandidates = async () => {
        try {
          console.log("Fetching candidates for job:", selectedJob.id);
          const response = await fetch(`${API_BASE_URL}/api/applications/${selectedJob.id}`);
          const data = await response.json();
          setCandidates(Array.isArray(data) ? data : []);
          setLastUpdated(new Date().toLocaleString());
        } catch (error) {
          console.error("Failed to fetch candidates:", error);
          setCandidates([]);
        }
      };
      fetchCandidates();
    } else {
      setCandidates([]);
    }
  }, [selectedJob]);

  const handleRefresh = () => {
    if (selectedJob) {
      setIsRefreshing(true);
      const fetchCandidates = async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/applications/${selectedJob.id}`);
          const data = await response.json();
          setCandidates(data);
          setLastUpdated(new Date().toLocaleString());
        } catch (error) {
          console.error("Failed to fetch candidates:", error);
        } finally {
          setTimeout(() => setIsRefreshing(false), 1000); // Ensure animation runs for 1s
        }
      };
      fetchCandidates();
    }
  }

    const handleFileUpload = () => {
    if (!selectedJob) {
      alert("Please select a job first before uploading resumes.");
      return;
    }

    const input = document.createElement("input")
    input.type = "file"
    input.multiple = true
    input.accept = ".pdf"
    input.onchange = async (e) => {
      const files = (e.target as HTMLInputElement).files
      if (files && files.length > 0) {
        setIsUploading(true);
        const formData = new FormData();
        Array.from(files).forEach(file => {
          formData.append("pdf_files", file);
        });
        formData.append("job_title", selectedJob.title);

        try {
          const response = await fetch(`${API_BASE_URL}/api/upload`, {
            method: 'POST',
            body: formData,
          });
          const result = await response.json();
          console.log("Upload result:", result);
          handleRefresh(); 
        } catch (error) {
          console.error("File upload failed:", error);
        } finally {
          setIsUploading(false);
        }
      }
    }
    input.click()
  }

  const handleCreateJob = async () => {
    if (!newJobTitle.trim() || !newJobDescription.trim()) {
      alert("Please fill in both title and description");
      return;
    }

    setIsCreatingJob(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/jobs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newJobTitle.trim(),
          description: newJobDescription.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const newJob = await response.json();
      console.log("Job created:", newJob);
      
      // Refresh jobs list
      const jobsResponse = await fetch(`${API_BASE_URL}/api/jobs`);
      const updatedJobs = await jobsResponse.json();
      setJobs(updatedJobs);
      
      // Reset form and close modal
      setNewJobTitle("");
      setNewJobDescription("");
      setShowCreateJobModal(false);
      
    } catch (error) {
      console.error("Failed to create job:", error);
      alert("Failed to create job. Please try again.");
    } finally {
      setIsCreatingJob(false);
    }
  };

  const handleJobDescriptionClick = () => {
    if (selectedJob) {
      setEditingJobDescription(selectedJob.description || "");
      setShowJobDescriptionModal(true);
    }
  };

  const handleUpdateJobDescription = async () => {
    if (!selectedJob || !editingJobDescription.trim()) {
      alert("Please enter a job description");
      return;
    }

    setIsUpdatingJob(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/jobs/${selectedJob.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: selectedJob.title,
          description: editingJobDescription.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const updatedJob = await response.json();
      console.log("Job updated:", updatedJob);
      
      // Update selected job and jobs list
      setSelectedJob(updatedJob);
      setJobs(jobs.map(job => job.id === updatedJob.id ? updatedJob : job));
      
      // Close modal
      setShowJobDescriptionModal(false);
      
    } catch (error) {
      console.error("Failed to update job:", error);
      alert("Failed to update job description. Please try again.");
    } finally {
      setIsUpdatingJob(false);
    }
  };

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
      
      // Poll for completion with improved logic
      let pollAttempts = 0;
      const maxPollAttempts = 20; // 20 attempts * 3 seconds = 60 seconds max
      
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

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortColumn(column)
      setSortDirection("asc")
    }
  }

  const getSortIcon = (column: string) => {
    if (sortColumn !== column) {
      return <ArrowUpDown className="ml-1 h-4 w-4 text-gray-400" />
    }
    return sortDirection === "asc" ? (
      <ArrowUp className="ml-1 h-4 w-4 text-blue-600" />
    ) : (
      <ArrowDown className="ml-1 h-4 w-4 text-blue-600" />
    )
  }

  const handleFinalStatusChange = async (applicationId: number, newStatus: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/applications/${applicationId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ final_status: newStatus }),
      });
      // Refresh local data
      setCandidates(
        candidates.map((app) =>
          app.id === applicationId ? { ...app, final_status: newStatus } : app,
        ),
      );
    } catch (error) {
      console.error("Failed to update final status:", error);
    }
  }

  const handleFileOpen = (fileUrl: string, candidateName: string) => {
    // In a real application, this would open/download the actual file
    console.log(`Opening file for ${candidateName}: ${fileUrl}`)
    // Simulate file opening
    window.open(fileUrl, "_blank")
  }

  const sortedCandidates = [...(candidates || [])].sort((a, b) => {
    if (!sortColumn) return 0

    let aValue, bValue;

    if (sortColumn === 'name') {
      aValue = a.candidate.name;
      bValue = b.candidate.name;
    } else {
      aValue = a[sortColumn];
      bValue = b[sortColumn];
    }

    // Handle different data types
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      // numeric sort
    } else if (sortColumn === "last_updated" || sortColumn === "applied_on") {
      aValue = new Date(aValue)
      bValue = new Date(bValue)
    } else {
      aValue = String(aValue).toLowerCase()
      bValue = String(bValue).toLowerCase()
    }

    if (aValue < bValue) return sortDirection === "asc" ? -1 : 1
    if (aValue > bValue) return sortDirection === "asc" ? 1 : -1
    return 0
  })

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
  }, []);

  // System status helper functions
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between">
          <div></div>
          <h1 className="text-3xl font-bold text-center text-gray-900">Wheat From Chaff</h1>
          <div className="flex items-center space-x-3">
            <User className="h-5 w-5 text-gray-600" />
            <div className="text-right">
              <div className="text-sm font-medium text-gray-900">{userInfo.name}</div>
              <div className="text-xs text-gray-600">{userInfo.email}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-8 py-6">
        {/* Top Controls */}
        <div className="flex items-center justify-between mb-8">
          {/* Job Selection */}
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700">Job Title:</label>
            <Popover open={open} onOpenChange={setOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={open}
                  className="w-[300px] justify-between bg-transparent"
                >
                  {selectedJob?.title || "Select job title..."}
                  <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[300px] p-0">
                <Command>
                  <CommandInput placeholder="Search job titles..." />
                  <CommandList>
                    <CommandEmpty>No job title found.</CommandEmpty>
                    <CommandGroup>
                      {jobs.map((job, index) => (
                        <CommandItem
                          key={job.id ? `job-${job.id}` : `job-${index}`}
                          value={job.title}
                          onSelect={() => {
                            setSelectedJob(job);
                            setOpen(false);
                          }}
                        >
                          <Check className={cn("mr-2 h-4 w-4", selectedJob?.id === job.id ? "opacity-100" : "opacity-0")} />
                          {job.title}
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
            
            {/* Job Description Button */}
            {selectedJob && (
              <Button
                variant="outline"
                size="icon"
                onClick={handleJobDescriptionClick}
                className="bg-transparent"
                title="View/Edit Job Description"
              >
                <FileText className="h-4 w-4" />
              </Button>
            )}
            
            {/* Create Job Button */}
            <Dialog open={showCreateJobModal} onOpenChange={setShowCreateJobModal}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="flex items-center space-x-2">
                  <Plus className="h-4 w-4" />
                  <span>Create Job</span>
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Create New Job</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">Job Title</label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="e.g., Senior Software Engineer"
                      value={newJobTitle}
                      onChange={(e) => setNewJobTitle(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">Job Description</label>
                    <textarea
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-vertical"
                      placeholder="Enter the complete job description, requirements, and qualifications..."
                      value={newJobDescription}
                      onChange={(e) => setNewJobDescription(e.target.value)}
                      rows={8}
                    />
                  </div>
                  <div className="flex justify-end space-x-3 pt-4">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowCreateJobModal(false);
                        setNewJobTitle("");
                        setNewJobDescription("");
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleCreateJob}
                      disabled={isCreatingJob || !newJobTitle.trim() || !newJobDescription.trim()}
                    >
                      {isCreatingJob ? "Creating..." : "Create Job"}
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            
            {/* Model Selector Button */}
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
                        onClick={() => handleModelSwap(modelName, modeKey)}
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
          </div>

          {/* Right Controls */}
          <div className="flex flex-col items-end space-y-3">
            <div className="flex items-center space-x-4">
              <Button 
                onClick={handleFileUpload} 
                disabled={isUploading || modelStatus === "offline" || currentModel?.status === "swapping"} 
                className="flex items-center space-x-2"
              >
                <Upload className={cn("h-4 w-4", isUploading && "animate-pulse")} />
                <span>{isUploading ? "Uploading..." : "Upload Resumes"}</span>
              </Button>
              <Button variant="outline" onClick={handleRefresh} className="flex items-center space-x-2 bg-transparent">
                <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin-slow")} />
                <span>Refresh</span>
              </Button>
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
            </div>
            {isClient && <div className="text-sm text-gray-500">Last Updated: {lastUpdated}</div>}
          </div>
        </div>

        {/* Job Description Modal */}
        <Dialog open={showJobDescriptionModal} onOpenChange={setShowJobDescriptionModal}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>{selectedJob?.title}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">Job Description</label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-vertical"
                  placeholder="Enter the job description, requirements, and qualifications..."
                  value={editingJobDescription}
                  onChange={(e) => setEditingJobDescription(e.target.value)}
                  rows={12}
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowJobDescriptionModal(false);
                    setEditingJobDescription("");
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleUpdateJobDescription}
                  disabled={isUpdatingJob || !editingJobDescription.trim()}
                >
                  {isUpdatingJob ? "Saving..." : "Save"}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Table */}
        {selectedJob ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Candidates for {selectedJob.title}</h2>
              <p className="text-sm text-gray-600 mt-1">
                {candidates.length} candidate{candidates.length !== 1 ? "s" : ""} found
              </p>
            </div>

            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16">
                      <button
                        onClick={() => handleSort("id")}
                        className="flex items-center hover:text-gray-900 transition-colors"
                      >
                        ID
                        {getSortIcon("id")}
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        onClick={() => handleSort("name")}
                        className="flex items-center hover:text-gray-900 transition-colors"
                      >
                        Name
                        {getSortIcon("name")}
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        onClick={() => handleSort("last_updated")}
                        className="flex items-center hover:text-gray-900 transition-colors"
                      >
                        Last Updated
                        {getSortIcon("last_updated")}
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        onClick={() => handleSort("status")}
                        className="flex items-center hover:text-gray-900 transition-colors"
                      >
                        AI Status
                        {getSortIcon("status")}
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        onClick={() => handleSort("applied_on")}
                        className="flex items-center hover:text-gray-900 transition-colors"
                      >
                        Applied On
                        {getSortIcon("applied_on")}
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        onClick={() => handleSort("reason")}
                        className="flex items-center hover:text-gray-900 transition-colors"
                      >
                        AI-Generated Reason
                        {getSortIcon("reason")}
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        onClick={() => handleSort("final_status")}
                        className="flex items-center hover:text-gray-900 transition-colors"
                      >
                        Final Status
                        {getSortIcon("final_status")}
                      </button>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedCandidates.map((app) => (
                    <TableRow key={app.id}>
                      <TableCell className="font-medium">{app.candidate.id}</TableCell>
                      <TableCell className="font-medium">{app.candidate.name}</TableCell>
                      <TableCell className="text-gray-600">{isClient && new Date(app.last_updated).toLocaleString()}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(app.status)}
                          {getStatusBadge(app.status)}
                          <button
                            onClick={() => handleFileOpen(app.file_url, app.candidate.name)}
                            className="ml-2 p-1 hover:bg-gray-100 rounded transition-colors"
                            title={`Open file for ${app.candidate.name}`}
                          >
                            <ExternalLink className="h-4 w-4 text-gray-500 hover:text-blue-600" />
                          </button>
                        </div>
                      </TableCell>
                      <TableCell className="text-gray-600">{isClient && new Date(app.applied_on).toLocaleString()}</TableCell>
                      <TableCell className="text-gray-600 max-w-xs">
                        <div className="truncate" title={app.reason}>
                          {app.reason}
                        </div>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <button className="flex items-center space-x-2 hover:bg-gray-50 p-2 rounded transition-colors">
                              {getStatusIcon(app.final_status)}
                              {getStatusBadge(app.final_status)}
                              <ChevronDown className="h-3 w-3 text-gray-400" />
                            </button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {["Shortlisted", "Needs Review", "Rejected"].map((status) => (
                              <DropdownMenuItem
                                key={status}
                                onClick={() => handleFinalStatusChange(app.id, status)}
                                className="flex items-center space-x-2"
                              >
                                {getStatusIcon(status)}
                                <span>{status}</span>
                              </DropdownMenuItem>
                            ))}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <div className="text-gray-400 mb-4">
              <AlertCircle className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Job Selected</h3>
            <p className="text-gray-600">Please select a job title from the dropdown to view candidates.</p>
          </div>
        )}
      </div>
    </div>
  )
}
