import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"

interface Job {
  id: number
  title: string
  description: string
}

interface JobDescriptionModalProps {
  showJobDescriptionModal: boolean
  setShowJobDescriptionModal: (show: boolean) => void
  selectedJob: Job | null
  editingJobDescription: string
  setEditingJobDescription: (description: string) => void
  isUpdatingJob: boolean
  onUpdateJobDescription: () => void
}

export function JobDescriptionModal({
  showJobDescriptionModal,
  setShowJobDescriptionModal,
  selectedJob,
  editingJobDescription,
  setEditingJobDescription,
  isUpdatingJob,
  onUpdateJobDescription
}: JobDescriptionModalProps) {
  return (
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
              onClick={onUpdateJobDescription}
              disabled={isUpdatingJob || !editingJobDescription.trim()}
            >
              {isUpdatingJob ? "Saving..." : "Save"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
