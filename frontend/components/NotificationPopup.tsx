import React from 'react'
import { CheckCircle, XCircle, X } from 'lucide-react'

interface ProcessingResult {
  success: number
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

  const isAllSuccess = message.llm_error === 0 && message.server_error === 0
  const hasErrors = message.llm_error > 0 || message.server_error > 0

  return (
    <div 
      className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 max-w-md w-full mx-4 p-4 rounded-lg shadow-lg border-l-4 ${
        isAllSuccess 
          ? 'bg-green-50 border-green-400 text-green-800' 
          : 'bg-red-50 border-red-400 text-red-800'
      } animate-slide-down`}
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {isAllSuccess ? (
            <CheckCircle className="h-5 w-5 text-green-400" />
          ) : (
            <XCircle className="h-5 w-5 text-red-400" />
          )}
        </div>
        
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${
            isAllSuccess ? 'text-green-800' : 'text-red-800'
          }`}>
            {isAllSuccess ? 'Processing Complete' : 'Processing Complete with Errors'}
          </h3>
          
          <div className={`mt-2 text-sm ${
            isAllSuccess ? 'text-green-700' : 'text-red-700'
          }`}>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span>✅ Successful:</span>
                <span className="font-semibold">{message.success}</span>
              </div>
              
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
              isAllSuccess 
                ? 'text-green-400 hover:bg-green-100 focus:ring-green-500' 
                : 'text-red-400 hover:bg-red-100 focus:ring-red-500'
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
