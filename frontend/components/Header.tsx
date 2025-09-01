import { User } from "lucide-react"

interface HeaderProps {
  userInfo: {
    name: string
    email: string
  }
}

export function Header({ userInfo }: HeaderProps) {
  return (
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
  )
}
