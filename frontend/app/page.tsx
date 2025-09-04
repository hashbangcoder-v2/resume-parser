"use client"

import { useState, useEffect } from "react"
import { Header } from "@/components/Header"
import { JobSelector } from "@/components/JobSelector"
import { ModelSelector } from "@/components/ModelSelector"
import { CreateJobModal } from "@/components/CreateJobModal"
import { JobDescriptionModal } from "@/components/JobDescriptionModal"
import { ControlButtons } from "@/components/ControlButtons"
import { CandidatesTable } from "@/components/CandidatesTable"
import { NotificationPopup } from "@/components/NotificationPopup"
import { useJobs } from "@/hooks/useJobs"
import { useModels } from "@/hooks/useModels"
import { useCandidates } from "@/hooks/useCandidates"
import { useSystemStatus } from "@/hooks/useSystemStatus"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export default function CandidateDashboard() {
  // Client-side rendering check
  const [isClient, setIsClient] = useState(false)
  
  // UI state
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [showCreateJobModal, setShowCreateJobModal] = useState(false)
  const [newJobTitle, setNewJobTitle] = useState("")
  const [newJobDescription, setNewJobDescription] = useState("")
  const [isCreatingJob, setIsCreatingJob] = useState(false)
  const [showJobDescriptionModal, setShowJobDescriptionModal] = useState(false)
  const [editingJobDescription, setEditingJobDescription] = useState("")
  const [isUpdatingJob, setIsUpdatingJob] = useState(false)
  const [userInfo, setUserInfo] = useState({ name: "", email: "" })
  
  // Notification state
  const [showNotification, setShowNotification] = useState(false)
  const [notificationMessage, setNotificationMessage] = useState<{
    success: number
    llm_error: number
    server_error: number
    total: number
  } | null>(null)

  // Custom hooks for data management
  const { jobs, selectedJob, setSelectedJob, refreshJobs, setJobs } = useJobs()
  const { availableModels, currentModel, modelStatus, isSwappingModel, handleModelSwap, setModelStatus } = useModels()
  const { candidates, sortColumn, sortDirection, lastUpdated, refreshCandidates, handleSort, handleFinalStatusChange, handleFileOpen } = useCandidates(selectedJob)
  const { backendStatus } = useSystemStatus(setModelStatus)

  useEffect(() => {
    setIsClient(true)
  }, [])
  
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

  const handleRefresh = () => {
    if (selectedJob) {
      setIsRefreshing(true);
      refreshCandidates().finally(() => {
          setTimeout(() => setIsRefreshing(false), 1000); // Ensure animation runs for 1s
      });
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
          
          // Show notification with processing results
          if (result.message) {
            setNotificationMessage(result.message);
            setShowNotification(true);
            
            // Auto-hide notification after 8 seconds
            setTimeout(() => {
              setShowNotification(false);
            }, 8000);
          }
          
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
      await refreshJobs();
      
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Header userInfo={userInfo} />
      
      {/* Notification Popup */}
      <NotificationPopup
        isVisible={showNotification}
        message={notificationMessage}
        onClose={() => setShowNotification(false)}
      />

      {/* Main Content */}
      <div className="px-8 py-6">
        {/* Top Controls */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <JobSelector
              jobs={jobs}
              selectedJob={selectedJob}
              onJobSelect={setSelectedJob}
              onJobDescriptionClick={handleJobDescriptionClick}
            />
            
            <CreateJobModal
              showCreateJobModal={showCreateJobModal}
              setShowCreateJobModal={setShowCreateJobModal}
              newJobTitle={newJobTitle}
              setNewJobTitle={setNewJobTitle}
              newJobDescription={newJobDescription}
              setNewJobDescription={setNewJobDescription}
              isCreatingJob={isCreatingJob}
              onCreateJob={handleCreateJob}
            />
            
            <ModelSelector
              availableModels={availableModels}
              currentModel={currentModel}
              isSwappingModel={isSwappingModel}
              onModelSwap={handleModelSwap}
            />
          </div>

          <ControlButtons
            isUploading={isUploading}
            isRefreshing={isRefreshing}
            modelStatus={modelStatus}
            currentModel={currentModel}
            backendStatus={backendStatus}
            lastUpdated={lastUpdated}
            isClient={isClient}
            onFileUpload={handleFileUpload}
            onRefresh={handleRefresh}
          />
        </div>

        <JobDescriptionModal
          showJobDescriptionModal={showJobDescriptionModal}
          setShowJobDescriptionModal={setShowJobDescriptionModal}
          selectedJob={selectedJob}
          editingJobDescription={editingJobDescription}
          setEditingJobDescription={setEditingJobDescription}
          isUpdatingJob={isUpdatingJob}
          onUpdateJobDescription={handleUpdateJobDescription}
        />

        <CandidatesTable
          selectedJob={selectedJob}
          candidates={candidates}
          sortColumn={sortColumn}
          sortDirection={sortDirection}
          isClient={isClient}
          onSort={handleSort}
          onFinalStatusChange={handleFinalStatusChange}
          onFileOpen={handleFileOpen}
        />
      </div>
    </div>
  )
}