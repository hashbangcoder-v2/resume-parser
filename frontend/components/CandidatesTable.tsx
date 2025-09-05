import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import {
  ChevronDown,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileX,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ExternalLink,
} from "lucide-react"

interface Candidate {
  id: number
  name: string
}

interface Application {
  id: number
  candidate: Candidate | null  // Allow null for invalid applications
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

interface CandidatesTableProps {
  selectedJob: Job | null
  candidates: Application[]
  sortColumn: string | null
  sortDirection: "asc" | "desc"
  isClient: boolean
  showInvalid: boolean
  onShowInvalidChange: (show: boolean) => void
  onSort: (column: string) => void
  onFinalStatusChange: (applicationId: number, newStatus: string) => void
  onFileOpen: (fileUrl: string, candidateName: string) => void
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case "Shortlisted":
      return <CheckCircle className="h-4 w-4 text-green-600" />
    case "Rejected":
      return <XCircle className="h-4 w-4 text-red-600" />
    case "Needs Review":
      return <AlertCircle className="h-4 w-4 text-yellow-600" />
    case "Invalid":
      return <FileX className="h-4 w-4 text-gray-600" />
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
    case "Invalid":
      return <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-100">{status}</Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

const getFinalStatusIcon = (status: string) => {
  switch (status) {
    case "Accepted":
      return <CheckCircle className="h-4 w-4 text-green-600" />
    case "Rejected":
      return <XCircle className="h-4 w-4 text-red-600" />
    case "Invalid":
      return <FileX className="h-4 w-4 text-gray-600" />
    default:
      return <AlertCircle className="h-4 w-4 text-gray-400" />
  }
}

const getFinalStatusBadge = (status: string) => {
  switch (status) {
    case "Accepted":
      return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">{status}</Badge>
    case "Rejected":
      return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">{status}</Badge>
    case "Invalid":
      return <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-100">{status}</Badge>
    default:
      return <Badge variant="secondary">Pending</Badge>
  }
}

export function CandidatesTable({
  selectedJob,
  candidates,
  sortColumn,
  sortDirection,
  isClient,
  showInvalid,
  onShowInvalidChange,
  onSort,
  onFinalStatusChange,
  onFileOpen
}: CandidatesTableProps) {
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

  const sortedCandidates = [...(candidates || [])].sort((a, b) => {
    if (!sortColumn) return 0

    let aValue: any, bValue: any;

    if (sortColumn === 'name') {
      aValue = a.candidate?.name || '';  // Handle null candidate
      bValue = b.candidate?.name || '';  // Handle null candidate
    } else {
      // Type-safe property access
      aValue = (a as any)[sortColumn];
      bValue = (b as any)[sortColumn];
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

  if (!selectedJob) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
        <div className="text-gray-400 mb-4">
          <AlertCircle className="h-12 w-12 mx-auto" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Job Selected</h3>
        <p className="text-gray-600">Please select a job title from the dropdown to view candidates.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Candidates for {selectedJob.title}</h2>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="show-invalid"
              checked={showInvalid}
              onChange={(e) => onShowInvalidChange(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label 
              htmlFor="show-invalid" 
              className="text-sm font-medium text-gray-700 cursor-pointer"
            >
              Show Invalid
            </label>
          </div>
        </div>
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
                  onClick={() => onSort("id")}
                  className="flex items-center hover:text-gray-900 transition-colors"
                >
                  ID
                  {getSortIcon("id")}
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => onSort("name")}
                  className="flex items-center hover:text-gray-900 transition-colors"
                >
                  Name
                  {getSortIcon("name")}
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => onSort("last_updated")}
                  className="flex items-center hover:text-gray-900 transition-colors"
                >
                  Last Updated
                  {getSortIcon("last_updated")}
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => onSort("status")}
                  className="flex items-center hover:text-gray-900 transition-colors"
                >
                  AI Status
                  {getSortIcon("status")}
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => onSort("applied_on")}
                  className="flex items-center hover:text-gray-900 transition-colors"
                >
                  Applied On
                  {getSortIcon("applied_on")}
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => onSort("reason")}
                  className="flex items-center hover:text-gray-900 transition-colors"
                >
                  AI-Generated Reason
                  {getSortIcon("reason")}
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => onSort("final_status")}
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
                <TableCell className="font-medium">{app.candidate?.id || '-'}</TableCell>
                <TableCell className="font-medium">
                  {app.candidate?.name || <span className="text-gray-400 italic">Invalid Document</span>}
                </TableCell>
                <TableCell className="text-gray-600">{isClient && new Date(app.last_updated).toLocaleString()}</TableCell>
                <TableCell>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(app.status)}
                    {getStatusBadge(app.status)}
                    <button
                      onClick={() => onFileOpen(app.file_url, app.candidate?.name || 'Invalid Document')}
                      className="ml-2 p-1 hover:bg-gray-100 rounded transition-colors"
                      title={`Open file for ${app.candidate?.name || 'Invalid Document'}`}
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
                        {getFinalStatusIcon(app.final_status)}
                        {getFinalStatusBadge(app.final_status)}
                        <ChevronDown className="h-3 w-3 text-gray-400" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {["Accepted", "Rejected"].map((status) => (
                        <DropdownMenuItem
                          key={status}
                          onClick={() => onFinalStatusChange(app.id, status)}
                          className="flex items-center space-x-2"
                        >
                          {getFinalStatusIcon(status)}
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
  )
}
