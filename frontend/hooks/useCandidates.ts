import { useState, useEffect } from "react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

interface Candidate {
  id: number
  name: string
}

interface Application {
  id: number
  candidate: Candidate
  status: string
  last_updated: string
  applied_on: string
  reason: string
  final_status: string
  file_url: string
}

interface Job {
  id: number
  title: string
  description: string
}

export function useCandidates(selectedJob: Job | null) {
  const [candidates, setCandidates] = useState<Application[]>([])
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc")
  const [lastUpdated, setLastUpdated] = useState(new Date().toLocaleString())

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

  const refreshCandidates = async () => {
    if (selectedJob) {
      try {
        const response = await fetch(`${API_BASE_URL}/api/applications/${selectedJob.id}`);
        const data = await response.json();
        setCandidates(data);
        setLastUpdated(new Date().toLocaleString());
      } catch (error) {
        console.error("Failed to fetch candidates:", error);
      }
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

  const handleFinalStatusChange = async (applicationId: number, newStatus: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/applications/${applicationId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ final_status: newStatus }),
      });
      
      if (response.ok) {
        const updatedApplication = await response.json();
        // Update local data with the response from server (includes updated last_updated timestamp)
        setCandidates(
          candidates.map((app) =>
            app.id === applicationId ? {
              ...app,
              final_status: newStatus,
              last_updated: updatedApplication.last_updated
            } : app,
          ),
        );
        setLastUpdated(new Date().toLocaleString()); // Update the global "last updated" indicator
      } else {
        throw new Error('Failed to update status');
      }
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

  return {
    candidates,
    sortColumn,
    sortDirection,
    lastUpdated,
    refreshCandidates,
    handleSort,
    handleFinalStatusChange,
    handleFileOpen
  }
}
