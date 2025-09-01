import { useState, useEffect } from "react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

interface Job {
  id: number
  title: string
  description: string
}

export function useJobs() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)

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

  const refreshJobs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/jobs`);
      const data = await response.json();
      setJobs(data);
    } catch (error) {
      console.error("Failed to refresh jobs:", error);
    }
  };

  return {
    jobs,
    selectedJob,
    setSelectedJob,
    refreshJobs,
    setJobs
  }
}
