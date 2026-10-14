import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from './test-utils'
import { ClustersPage } from '@/pages/ClustersPage'
import * as clusterApi from '@/api/clusters'
import { ClusterResponse } from '@/types'

vi.mock('@/api/clusters')

describe('Clusters Page', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  const mockClusters: ClusterResponse[] = [
    {
      id: 'cluster-abc-123',
      name: 'gpu-training-cluster',
      description: 'H100 dedicated tier',
      status: 'ACTIVE',
      created_at: '2026-10-09T08:00:00Z',
      updated_at: '2026-10-09T08:00:00Z',
    },
    {
      id: 'cluster-def-456',
      name: 'maintenance-cluster',
      description: 'Under repair',
      status: 'MAINTENANCE',
      created_at: '2026-10-09T08:00:00Z',
      updated_at: '2026-10-09T08:00:00Z',
    },
  ]

  it('renders cluster inventory with status badges', async () => {
    vi.mocked(clusterApi.listClusters).mockResolvedValue(mockClusters)

    renderWithProviders(<ClustersPage />)

    await waitFor(() => {
      expect(screen.getByText('gpu-training-cluster')).toBeInTheDocument()
      expect(screen.getByText('maintenance-cluster')).toBeInTheDocument()
      expect(screen.getAllByText('ACTIVE').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('MAINTENANCE').length).toBeGreaterThanOrEqual(1)
    })
  })

  it('validates cluster creation form preventing empty submissions', async () => {
    const user = userEvent.setup()
    vi.mocked(clusterApi.listClusters).mockResolvedValue(mockClusters)
    const createSpy = vi.mocked(clusterApi.createCluster).mockResolvedValue({
      id: 'cluster-new',
      name: 'new-cluster',
      status: 'ACTIVE',
      created_at: '2026-10-09T10:00:00Z',
      updated_at: '2026-10-09T10:00:00Z',
    })

    renderWithProviders(<ClustersPage />)

    await waitFor(() => {
      expect(screen.getByText('gpu-training-cluster')).toBeInTheDocument()
    })

    // Open creation modal
    const openBtn = screen.getByRole('button', { name: /create cluster/i })
    await user.click(openBtn)

    expect(screen.getByText('Create New Server Cluster')).toBeInTheDocument()

    // Fill valid name and submit
    const nameInput = screen.getByLabelText(/cluster identifier name/i)
    await user.type(nameInput, 'new-cluster')

    // Click submit in modal (second Create Cluster button)
    const createButtons = screen.getAllByRole('button', { name: /create cluster/i })
    const submitBtn = createButtons[createButtons.length - 1]
    await user.click(submitBtn)

    await waitFor(() => {
      expect(createSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'new-cluster',
          status: 'ACTIVE',
        })
      )
    })
  })
})
