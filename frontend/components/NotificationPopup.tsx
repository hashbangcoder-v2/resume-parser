import React from 'react'
import { CheckCircle, XCircle, X, AlertCircle } from 'lucide-react'

interface ProcessingResult {
  success: number
  skipped: number
  llm_error: number
  server_error: number
  total: number
}

interface NotificationPopupProps {
  isVisible: boolean
  message: ProcessingResult | null
  onClose: () => void
}

export function NotificationPopup({ isVisible, message, onClose }: NotificationPopupProps) {
  if (!isVisible || !message) return null

  const hasErrors = message.llm_error > 0 || message.server_error > 0
  const hasSkipped = message.skipped > 0
  const noErrors = !hasErrors
  
  // Determine notification color/state
  const isGreen = noErrors && !hasSkipped  // Only successes, no errors, no skipped
  const isYellow = noErrors && hasSkipped  // No errors but has skipped items
  const isRed = hasErrors                  // Any errors (regardless of success/skipped)

  return (
    <div 
      className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 max-w-md w-full mx-4 p-4 rounded-lg shadow-lg border-l-4 ${
        isGreen 
          ? 'bg-green-50 border-green-400 text-green-800' 
          : isYellow ? 'bg-yellow-50 border-yellow-400 text-yellow-800' : 'bg-red-50 border-red-400 text-red-800'
      } animate-slide-down`}
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {isGreen ? (
            <CheckCircle className="h-5 w-5 text-green-400" />
          ) : isYellow ? (
            <AlertCircle className="h-5 w-5 text-yellow-400" />
          ) : (
            <XCircle className="h-5 w-5 text-red-400" />
          )}
        </div>
        
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${
            isGreen ? 'text-green-800' : isYellow ? 'text-yellow-800' : 'text-red-800'
          }`}>
            {isGreen ? 'Processing Complete' : isYellow ? 'Processing Complete with Skipped' : 'Processing Complete with Errors'}
          </h3>
          
          <div className={`mt-2 text-sm ${
            isGreen ? 'text-green-700' : isYellow ? 'text-yellow-700' : 'text-red-700'
          }`}>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span>✅ Successful:</span>
                <span className="font-semibold">{message.success}</span>
              </div>
              
              {message.skipped > 0 && (
                <div className="flex justify-between">
                  <span>⏭️ Skipped:</span>
                  <span className="font-semibold">{message.skipped}</span>
                </div>
              )}
              
              {message.llm_error > 0 && (
                <div className="flex justify-between">
                  <span>🤖 AI Processing Errors:</span>
                  <span className="font-semibold">{message.llm_error}</span>
                </div>
              )}
              
              {message.server_error > 0 && (
                <div className="flex justify-between">
                  <span>⚠️ Server Errors:</span>
                  <span className="font-semibold">{message.server_error}</span>
                </div>
              )}
              
              <div className="flex justify-between border-t pt-1 mt-2">
                <span className="font-medium">Total Processed:</span>
                <span className="font-bold">{message.total}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="ml-4 flex-shrink-0">
          <button
            className={`rounded-md p-1.5 inline-flex ${
              isGreen 
                ? 'text-green-400 hover:bg-green-100 focus:ring-green-500' 
                : isYellow ? 'text-yellow-400 hover:bg-yellow-100 focus:ring-yellow-500' : 'text-red-400 hover:bg-red-100 focus:ring-red-500'
            } hover:text-opacity-75 focus:outline-none focus:ring-2 focus:ring-offset-2`}
            onClick={onClose}
          >
            <span className="sr-only">Dismiss</span>
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
