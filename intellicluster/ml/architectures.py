"""
PyTorch neural network architectures for INTELLICLUSTER runtime inference.
Matches the exact layer parameters and dimensions of saved model checkpoints:
- ResourceLSTM: multivariate 2-layer LSTM for 24-hour resource forecasting
- QNetwork: Deep Q-Network MLP for workload placement benchmark
"""

import torch
import torch.nn as nn


class ResourceLSTM(nn.Module):
    """
    Multivariate 2-layer stacked LSTM network for multi-step resource forecasting.
    Checkpoint: ml_models/resource_forecasting_lstm.pt

    Input:
        x: Tensor of shape (batch_size, 168, 5)
           168-hour lookback window with 5 input features:
           [cpu_utilization, memory_usage, storage_usage, workload, Resource Allocation]
    Output:
        Tensor of shape (batch_size, 24, 3)
        24-hour horizon for 3 target features:
        [cpu_utilization, memory_usage, workload]
    """

    def __init__(
        self,
        in_dim: int = 5,
        h1: int = 64,
        h2: int = 32,
        out_horizon: int = 24,
        out_vars: int = 3,
        dropout_prob: float = 0.2,
    ) -> None:
        super().__init__()
        self.in_dim = in_dim
        self.h1 = h1
        self.h2 = h2
        self.out_horizon = out_horizon
        self.out_vars = out_vars

        self.lstm1 = nn.LSTM(in_dim, h1, batch_first=True)
        self.dropout = nn.Dropout(dropout_prob)
        self.lstm2 = nn.LSTM(h1, h2, batch_first=True)
        self.fc = nn.Linear(h2, out_horizon * out_vars)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, 168, 5)
        out, _ = self.lstm1(x)
        out = self.dropout(out)
        out, _ = self.lstm2(out)
        last_step = out[:, -1, :]  # Take output of last sequence step
        preds = self.fc(last_step)
        return preds.view(-1, self.out_horizon, self.out_vars)


class QNetwork(nn.Module):
    """
    Deep Q-Network multi-layer perceptron for load-balancing action scoring.
    Checkpoint: ml_models/load_balancer_dqn.pt

    Input:
        x: Tensor of shape (batch_size, 25)
           25-dimensional continuous state vector:
           - 8 task demand features
           - 16 candidate node features (4 nodes x 4 metrics: free CPU ratio,
             free RAM ratio, normalized latency, normalized active tasks)
           - 1 background resource utilization scalar
    Output:
        Tensor of shape (batch_size, 4)
        Action Q-values for 4 node archetypes:
        [0: Edge_Micro, 1: Standard_Worker, 2: Compute_Dense, 3: Enterprise_Cluster]
    """

    def __init__(self, in_dim: int = 25, out_actions: int = 4) -> None:
        super().__init__()
        self.in_dim = in_dim
        self.out_actions = out_actions

        self.net = nn.Sequential(
            nn.Linear(in_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, out_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
