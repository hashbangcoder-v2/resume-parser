import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Plus } from "lucide-react"

interface CreateJobModalProps {
  showCreateJobModal: boolean
  setShowCreateJobModal: (show: boolean) => void
  newJobTitle: string
  setNewJobTitle: (title: string) => void
  newJobDescription: string
  setNewJobDescription: (description: string) => void
  isCreatingJob: boolean
  onCreateJob: () => void
}

export function CreateJobModal({
  showCreateJobModal,
  setShowCreateJobModal,
  newJobTitle,
  setNewJobTitle,
  newJobDescription,
  setNewJobDescription,
  isCreatingJob,
  onCreateJob
}: CreateJobModalProps) {
  return (
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
              onClick={onCreateJob}
              disabled={isCreatingJob || !newJobTitle.trim() || !newJobDescription.trim()}
            >
              {isCreatingJob ? "Creating..." : "Create Job"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
