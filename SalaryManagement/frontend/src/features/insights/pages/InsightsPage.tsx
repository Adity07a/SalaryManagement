
import { useState, type ReactNode } from "react";
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import AccountBalanceWalletOutlinedIcon from "@mui/icons-material/AccountBalanceWalletOutlined";
import TrendingUpOutlinedIcon from "@mui/icons-material/TrendingUpOutlined";
import QueryStatsOutlinedIcon from "@mui/icons-material/QueryStatsOutlined";

import { Link as RouterLink } from "react-router-dom";
import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { analyticsApi } from "../../../api/analytics";
import type { SalaryGroupBy } from "../../../api/types";
import { PayrollTrendsSection } from "../components/PayrollTrendsSection";

function formatUsd(value?: string | null): string {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return "—";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(amount);
}

function formatCompactUsd(value: string): string {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return value;
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(amount);
}

function MetricCard({
  label,
  value,
  description,
  icon,
}: {
  label: string;
  value: string;
  description: string;
  icon: ReactNode;
}) {
  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2.5,
        borderRadius: 3,
        minWidth: 0,
      }}
    >
      <Stack
        direction="row"
        alignItems="flex-start"
        justifyContent="space-between"
        spacing={2}
      >
        <Box sx={{ minWidth: 0 }}>
          <Typography
            variant="body2"
            color="text.secondary"
            fontWeight={600}
          >
            {label}
          </Typography>

          <Typography
            variant="h5"
            fontWeight={750}
            sx={{ mt: 1, overflowWrap: "anywhere" }}
          >
            {value}
          </Typography>
        </Box>

        <Box
          sx={{
            width: 42,
            height: 42,
            borderRadius: 2,
            bgcolor: "primary.light",
            color: "primary.dark",
            display: "grid",
            placeItems: "center",
            flexShrink: 0,
          }}
        >
          {icon}
        </Box>
      </Stack>

      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: "block", mt: 1.5 }}
      >
        {description}
      </Typography>
    </Paper>
  );
}

function SectionHeader({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      justifyContent="space-between"
      alignItems={{ xs: "flex-start", sm: "center" }}
      spacing={1.5}
      sx={{ mb: 2.5 }}
    >
      <Box>
        <Typography variant="h6">{title}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          {description}
        </Typography>
      </Box>

      {action}
    </Stack>
  );
}

const groupOptions: { value: SalaryGroupBy; label: string }[] = [
  { value: "department", label: "Department" },
  { value: "country", label: "Country" },
  { value: "job_title", label: "Job title" },
];

export function InsightsPage() {
  const [groupBy, setGroupBy] =
    useState<SalaryGroupBy>("department");

  const [outlierGroupBy, setOutlierGroupBy] =
    useState<SalaryGroupBy>("job_title");

  const summaryQuery = useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: ({ signal }) => analyticsApi.getSummary(signal),
  });

  const distributionQuery = useQuery({
    queryKey: ["analytics", "distribution"],
    queryFn: ({ signal }) => analyticsApi.getDistribution(signal),
  });

  const statsQuery = useQuery({
    queryKey: ["analytics", "salary-stats", groupBy],
    queryFn: ({ signal }) =>
      analyticsApi.getSalaryStats(groupBy, signal),
    placeholderData: keepPreviousData,
  });

  const outliersQuery = useQuery({
    queryKey: ["analytics", "outliers", outlierGroupBy],
    queryFn: ({ signal }) =>
      analyticsApi.getOutliers(outlierGroupBy, 1.5, signal),
    placeholderData: keepPreviousData,
  });

  const summary = summaryQuery.data;
  const buckets = distributionQuery.data?.buckets ?? [];
  const stats = statsQuery.data?.items ?? [];
  const outliers = outliersQuery.data?.items ?? [];

  const maxBucketCount = Math.max(
    1,
    ...buckets.map((bucket) => bucket.count),
  );

  const hasQueryError =
    summaryQuery.isError ||
    distributionQuery.isError ||
    statsQuery.isError ||
    outliersQuery.isError;

  return (
    <Stack spacing={2.5}>
      <Box>
        <Typography variant="h4">Salary Insights</Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Understand payroll costs, compensation differences and
          salary distribution across your organization.
        </Typography>

        <Chip
          size="small"
          label="All salary figures normalized to USD"
          variant="outlined"
          sx={{ mt: 1.5 }}
        />
      </Box>

      {hasQueryError && (
        <Alert severity="error">
          Some analytics could not be loaded. Check the backend logs
          and retry the affected section.
        </Alert>
      )}

      {/* Organization summary */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            sm: "repeat(2, minmax(0, 1fr))",
            xl: "repeat(4, minmax(0, 1fr))",
          },
          gap: 2,
        }}
      >
        
        <MetricCard
          label="Total employees"
          value={
            summary
              ? summary.headcount.toLocaleString()
              : summaryQuery.isLoading
                ? "Loading..."
                : "—"
          }
          description="Employees with current salary records"
          icon={<GroupsOutlinedIcon />}
        />

        <MetricCard
          label="Total payroll"
          value={
            summary
              ? formatUsd(summary.total_payroll_usd)
              : summaryQuery.isLoading
                ? "Loading..."
                : "—"
          }
          description="Combined current compensation in USD"
          icon={<AccountBalanceWalletOutlinedIcon />}
        />

        <MetricCard
          label="Average salary"
          value={
            summary
              ? formatUsd(summary.average_salary_usd)
              : summaryQuery.isLoading
                ? "Loading..."
                : "—"
          }
          description="Mean current salary across employees"
          icon={<TrendingUpOutlinedIcon />}
        />

        <MetricCard
          label="Median salary"
          value={
            summary
              ? formatUsd(summary.median_salary_usd)
              : summaryQuery.isLoading
                ? "Loading..."
                : "—"
          }
          description="Middle salary after sorting employees"
          icon={<QueryStatsOutlinedIcon />}
        />
      </Box>
      <PayrollTrendsSection />

      {/* Salary distribution */}
      <Paper
        variant="outlined"
        sx={{ p: { xs: 2, md: 2.5 }, borderRadius: 3 }}
      >
        <SectionHeader
          title="Salary distribution"
          description="Number of employees within each salary range."
        />

        {distributionQuery.isLoading ? (
          <Box sx={{ py: 4, display: "grid", placeItems: "center" }}>
            <CircularProgress size={28} />
          </Box>
        ) : distributionQuery.isError ? (
          <Alert severity="error">
            Unable to load salary distribution.
          </Alert>
        ) : buckets.length === 0 ? (
          <Typography color="text.secondary" variant="body2">
            No salary distribution data is available.
          </Typography>
        ) : (
          <Stack spacing={2.25}>
            {buckets.map((bucket, index) => {
              const percentage =
                (bucket.count / maxBucketCount) * 100;

              return (
                <Stack
                  key={`${bucket.bucket_start_usd}-${index}`}
                  direction={{ xs: "column", sm: "row" }}
                  alignItems={{ sm: "center" }}
                  spacing={1.5}
                >
                  <Typography
                    variant="body2"
                    sx={{ width: { sm: 175 }, flexShrink: 0 }}
                  >
                    {formatCompactUsd(bucket.bucket_start_usd)}
                    {" – "}
                    {formatCompactUsd(bucket.bucket_end_usd)}
                  </Typography>

                  <Box
                    sx={{
                      flex: 1,
                      width: "100%",
                      height: 13,
                      bgcolor: "action.hover",
                      borderRadius: 10,
                      overflow: "hidden",
                    }}
                  >
                    <Box
                      sx={{
                        height: "100%",
                        width: `${Math.max(percentage, bucket.count ? 1 : 0)}%`,
                        bgcolor: "primary.main",
                        borderRadius: 10,
                        transition: "width 250ms ease",
                      }}
                    />
                  </Box>

                  <Typography
                    variant="body2"
                    fontWeight={650}
                    sx={{
                      width: { sm: 75 },
                      textAlign: { sm: "right" },
                      flexShrink: 0,
                    }}
                  >
                    {bucket.count.toLocaleString()}
                  </Typography>
                </Stack>
              );
            })}
          </Stack>
        )}
      </Paper>

      {/* Salary statistics by group */}
      <Paper
        variant="outlined"
        sx={{ p: { xs: 2, md: 2.5 }, borderRadius: 3 }}
      >
        <SectionHeader
          title="Compensation comparison"
          description="Compare salary levels and percentiles across organizational groups."
          action={
            <FormControl size="small" sx={{ minWidth: 155 }}>
              <InputLabel id="stats-group-label">Group by</InputLabel>
              <Select
                labelId="stats-group-label"
                value={groupBy}
                label="Group by"
                onChange={(event) =>
                  setGroupBy(event.target.value as SalaryGroupBy)
                }
              >
                {groupOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          }
        />

        {statsQuery.isLoading ? (
          <Box sx={{ py: 4, display: "grid", placeItems: "center" }}>
            <CircularProgress size={28} />
          </Box>
        ) : statsQuery.isError ? (
          <Alert severity="error">
            Unable to load compensation comparisons.
          </Alert>
        ) : stats.length === 0 ? (
          <Typography color="text.secondary" variant="body2">
            No comparison data is available for this grouping.
          </Typography>
        ) : (
          <TableContainer>
            <Table size="small" sx={{ minWidth: 850 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Group</TableCell>
                  <TableCell align="right">Employees</TableCell>
                  <TableCell align="right">Minimum</TableCell>
                  <TableCell align="right">P25</TableCell>
                  <TableCell align="right">Median</TableCell>
                  <TableCell align="right">P75</TableCell>
                  <TableCell align="right">Maximum</TableCell>
                  <TableCell align="right">Average</TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {stats.map((item) => (
                  <TableRow key={item.group_value} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={650}>
                        {item.group_value}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {item.count.toLocaleString()}
                    </TableCell>
                    <TableCell align="right">
                      {formatUsd(item.min_usd)}
                    </TableCell>
                    <TableCell align="right">
                      {formatUsd(item.p25_usd)}
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight={700}>
                        {formatUsd(item.median_usd)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {formatUsd(item.p75_usd)}
                    </TableCell>
                    <TableCell align="right">
                      {formatUsd(item.max_usd)}
                    </TableCell>
                    <TableCell align="right">
                      {formatUsd(item.avg_usd)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Salary outliers */}
      <Paper
        variant="outlined"
        sx={{ p: { xs: 2, md: 2.5 }, borderRadius: 3 }}
      >
        <SectionHeader
          title="Salary outliers"
          description="Employees whose current salaries fall outside the 1.5 × IQR peer-group range."
          action={
            <FormControl size="small" sx={{ minWidth: 155 }}>
              <InputLabel id="outlier-group-label">
                Compare peers by
              </InputLabel>
              <Select
                labelId="outlier-group-label"
                value={outlierGroupBy}
                label="Compare peers by"
                onChange={(event) =>
                  setOutlierGroupBy(event.target.value as SalaryGroupBy)
                }
              >
                {groupOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          }
        />

        {outliersQuery.isLoading ? (
          <Box sx={{ py: 4, display: "grid", placeItems: "center" }}>
            <CircularProgress size={28} />
          </Box>
        ) : outliersQuery.isError ? (
          <Alert severity="error">
            Unable to load salary outliers.
          </Alert>
        ) : outliers.length === 0 ? (
          <Alert severity="success">
            No salary outliers were detected for this peer grouping.
          </Alert>
        ) : (
          <TableContainer>
            <Table size="small" sx={{ minWidth: 800 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Employee</TableCell>
                  <TableCell>Job title</TableCell>
                  <TableCell>Country</TableCell>
                  <TableCell align="right">Current salary</TableCell>
                  <TableCell align="right">Peer median</TableCell>
                  <TableCell align="right">Difference</TableCell>
                  <TableCell>Classification</TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {outliers.map((item) => (
                  <TableRow key={item.employee_id} hover>
                    <TableCell>
                      <Typography
                        component={RouterLink}
                        to={`/employees/${item.employee_id}`}
                        variant="body2"
                        fontWeight={650}
                        color="primary.main"
                        sx={{ textDecoration: "none" }}
                      >
                        {item.full_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {item.department}
                      </Typography>
                    </TableCell>

                    <TableCell>{item.job_title}</TableCell>
                    <TableCell>{item.country}</TableCell>

                    <TableCell align="right">
                      {formatUsd(item.salary_usd)}
                    </TableCell>

                    <TableCell align="right">
                      {formatUsd(item.peer_median_usd)}
                    </TableCell>

                    <TableCell align="right">
                      {Number(item.deviation_percent) > 0 ? "+" : ""}
                      {Number(item.deviation_percent).toFixed(2)}%
                    </TableCell>

                    <TableCell>
                      <Chip
                        size="small"
                        label={
                          item.direction === "high"
                            ? "Above range"
                            : "Below range"
                        }
                        color={
                          item.direction === "high" ? "warning" : "info"
                        }
                        variant="outlined"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Stack>
  );
}
