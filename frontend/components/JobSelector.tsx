import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Check, ChevronDown, FileText } from "lucide-react"
import { cn } from "@/lib/utils"

interface Job {
  id: number
  title: string
  description: string
}

interface JobSelectorProps {
  jobs: Job[]
  selectedJob: Job | null
  onJobSelect: (job: Job) => void
  onJobDescriptionClick: () => void
}

export function JobSelector({ jobs, selectedJob, onJobSelect, onJobDescriptionClick }: JobSelectorProps) {
  const [open, setOpen] = useState(false)

  return (
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
                      onJobSelect(job);
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
          onClick={onJobDescriptionClick}
          className="bg-transparent"
          title="View/Edit Job Description"
        >
          <FileText className="h-4 w-4" />
        </Button>
      )}
    </div>
  )
}
