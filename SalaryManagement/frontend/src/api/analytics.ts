
import { apiRequest } from "./client";

import type {
  DistributionResponse,
  OutliersResponse,
  SalaryGroupBy,
  SalaryStatsResponse,
  SummaryResponse,
} from "./types";

export const analyticsApi = {
  async getSummary(
    signal?: AbortSignal,
  ): Promise<SummaryResponse> {
    return apiRequest<SummaryResponse>(
      "/analytics/summary",
      { signal },
    );
  },

  async getSalaryStats(
    groupBy: SalaryGroupBy,
    signal?: AbortSignal,
  ): Promise<SalaryStatsResponse> {
    const query = new URLSearchParams({
      group_by: groupBy,
    });

    return apiRequest<SalaryStatsResponse>(
      `/analytics/salary-stats?${query}`,
      { signal },
    );
  },

  async getDistribution(
    signal?: AbortSignal,
  ): Promise<DistributionResponse> {
    return apiRequest<DistributionResponse>(
      "/analytics/distribution",
      { signal },
    );
  },

  async getOutliers(
    groupBy: SalaryGroupBy = "job_title",
    threshold = 1.5,
    signal?: AbortSignal,
  ): Promise<OutliersResponse> {
    const query = new URLSearchParams({
      group_by: groupBy,
      threshold: String(threshold),
    });

    return apiRequest<OutliersResponse>(
      `/analytics/outliers?${query}`,
      { signal },
    );
  },
};
