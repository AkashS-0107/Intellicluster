import { describe, it, expect } from 'vitest'
import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from './test-utils'
import { MlRegistryPage } from '@/pages/MlRegistryPage'

describe('ML Model Registry Page', () => {
  it('renders all model evaluation cards with offline baseline findings and caveats', () => {
    renderWithProviders(<MlRegistryPage />)

    // Check all models present
    expect(screen.getByText(/Model 1: Server Resource Clustering/i)).toBeInTheDocument()
    expect(screen.getByText(/Model 2A: Hardware Failure Prediction/i)).toBeInTheDocument()
    expect(screen.getByText(/Model 2B: Environmental Failure Prediction/i)).toBeInTheDocument()
    expect(screen.getByText(/Model 3: Temporal Resource Utilization Forecasting/i)).toBeInTheDocument()
    expect(screen.getByText(/Model 4A: Network Anomaly Detection/i)).toBeInTheDocument()
    expect(screen.getByText(/Model 4B: Infrastructure Anomaly Detection/i)).toBeInTheDocument()
    expect(screen.getByText(/Model 5: Dynamic Load Balancer & Scheduler/i)).toBeInTheDocument()

    // Check baseline metrics from prompt
    expect(screen.getByText('0.1478')).toBeInTheDocument() // Silhouette
    expect(screen.getByText('0.9748')).toBeInTheDocument() // Out-of-fold ROC-AUC 2A
    expect(screen.getByText('0.7281')).toBeInTheDocument() // Out-of-fold PR-AUC 2A
    expect(screen.getByText('87.32%')).toBeInTheDocument() // Recall
    expect(screen.getByText('38.64%')).toBeInTheDocument() // Precision
    expect(screen.getByText('14.81')).toBeInTheDocument() // Holdout MAE LSTM
    expect(screen.getByText('20.24')).toBeInTheDocument() // Holdout RMSE LSTM
    expect(screen.getByText('98.3%')).toBeInTheDocument() // DQN placement success
    expect(screen.getByText('154.6 CNY')).toBeInTheDocument() // DQN evaluated cost

    // Check operational decisions
    const rejectedBadges = screen.getAllByText('REJECTED')
    expect(rejectedBadges.length).toBeGreaterThanOrEqual(2) // 2B and 4A

    // Check 4-tier lifecycle levels
    expect(screen.getByText(/4-Tier Operational Readiness Lifecycle/i)).toBeInTheDocument()
    expect(screen.getAllByText(/Tier 1 of 4/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/Offline Validated Artifact/i)).toBeInTheDocument()
    expect(screen.getByText(/Backend Adapter Implemented/i)).toBeInTheDocument()
    expect(screen.getByText(/API Inference Endpoint Available/i)).toBeInTheDocument()
    expect(screen.getByText(/Live Prediction Confirmed/i)).toBeInTheDocument()
  })

  it('filters models interactively using status tabs', () => {
    renderWithProviders(<MlRegistryPage />)

    // Initially all 7 models should be visible
    expect(screen.getByText(/Offline Model Validation Audit \(7 of 7 Models\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Model 1: Server Resource Clustering/i)).toBeInTheDocument()
    expect(screen.getByText(/Model 4A: Network Anomaly Detection/i)).toBeInTheDocument()

    // Filter to Rejected
    const rejectedTab = screen.getByRole('button', { name: /Rejected/i })
    fireEvent.click(rejectedTab)

    expect(screen.getByText(/Offline Model Validation Audit \(2 of 7 Models\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Model 4A: Network Anomaly Detection/i)).toBeInTheDocument()
    expect(screen.queryByText(/Model 1: Server Resource Clustering/i)).not.toBeInTheDocument()

    // Filter to Validated
    const validatedTab = screen.getByRole('button', { name: /Validated/i })
    fireEvent.click(validatedTab)

    expect(screen.getByText(/Offline Model Validation Audit \(5 of 7 Models\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Model 1: Server Resource Clustering/i)).toBeInTheDocument()
    expect(screen.queryByText(/Model 4A: Network Anomaly Detection/i)).not.toBeInTheDocument()

    // Reset to All
    const allTab = screen.getByRole('button', { name: /All/i })
    fireEvent.click(allTab)

    expect(screen.getByText(/Offline Model Validation Audit \(7 of 7 Models\)/i)).toBeInTheDocument()
  })

  it('toggles model caveat details expand and collapse', () => {
    renderWithProviders(<MlRegistryPage />)

    // Caveat text initially rendered
    expect(screen.getByText(/Cluster distribution is balanced without singleton anomalies/i)).toBeInTheDocument()

    // Collapse first caveat
    const toggleBtns = screen.getAllByRole('button', { name: /Scientific Finding & Operational Caveat:/i })
    fireEvent.click(toggleBtns[0])

    // Should now be hidden
    expect(screen.queryByText(/Cluster distribution is balanced without singleton anomalies/i)).not.toBeInTheDocument()

    // Expand again
    fireEvent.click(toggleBtns[0])
    expect(screen.getByText(/Cluster distribution is balanced without singleton anomalies/i)).toBeInTheDocument()
  })
})
