import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Compass, ArrowLeft } from 'lucide-react'

export function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-[65vh] flex-col items-center justify-center text-center p-6 select-none">
      <div className="w-full max-w-md rounded-xl border border-[#DCE2ED] bg-white p-8 shadow-sm space-y-4">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#E8EEFF] border border-[#C7D7FE] text-[#244DE8] shadow-xs">
          <Compass className="w-7 h-7 stroke-[1.75]" />
        </div>

        <div className="space-y-2">
          <h1 className="text-xl font-bold font-mono text-[#101828] tracking-tight">
            404 — ROUTE NOT FOUND
          </h1>
          <p className="text-xs text-[#475467] leading-relaxed font-sans">
            The requested control endpoint does not exist in the active IntelliCluster navigation topology.
          </p>
        </div>

        <div className="pt-2">
          <Button
            variant="primary"
            size="sm"
            icon={<ArrowLeft className="w-4 h-4" />}
            onClick={() => navigate('/app')}
            className="w-full"
          >
            Return to Fleet Overview
          </Button>
        </div>
      </div>
    </div>
  )
}
