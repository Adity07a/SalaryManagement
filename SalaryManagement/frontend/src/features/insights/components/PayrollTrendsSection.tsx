
import { useState } from "react";
import {
  Alert,
  Box,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";

import { analyticsApi } from "../../../api/analytics";
import { employeeApi } from "../../../api/employees";
import type { PayrollTrendPoint } from "../../../api/types";

const CHART_WIDTH = 900;
const CHART_HEIGHT = 300;

const PLOT = {
  left: 85,
  right: 25,
  top: 25,
  bottom: 55,
};

function formatCurrency(value: string | number): string {
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

function formatCompactCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatMonth(value: string): string {
  const [year, month] = value.split("-").map(Number);

  if (!year || !month) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    year: "2-digit",
  }).format(new Date(year, month - 1, 1));
}

function PayrollLineChart({
  items,
}: {
  items: PayrollTrendPoint[];
}) {
  if (items.length === 0) {
    return (
      <Typography color="text.secondary" variant="body2">
        No historical payroll data is available.
      </Typography>
    );
  }

  const values = items.map((item) =>
    Number(item.total_payroll_usd),
  );

  const maxValue = Math.max(1, ...values);
  const chartMax = maxValue * 1.1;

  const plotWidth =
    CHART_WIDTH - PLOT.left - PLOT.right;

  const plotHeight =
    CHART_HEIGHT - PLOT.top - PLOT.bottom;

  const getX = (index: number) =>
    PLOT.left +
    (items.length === 1
      ? plotWidth / 2
      : (index / (items.length - 1)) * plotWidth);

  const getY = (value: number) =>
    PLOT.top +
    plotHeight -
    (value / chartMax) * plotHeight;

  const linePoints = values
    .map(
      (value, index) =>
        `${getX(index)},${getY(value)}`,
    )
    .join(" ");

  const areaPoints = [
    `${getX(0)},${PLOT.top + plotHeight}`,
    linePoints,
    `${getX(items.length - 1)},${PLOT.top + plotHeight}`,
  ].join(" ");

  const ticks = [0, 0.25, 0.5, 0.75, 1];

  const labelIndexes = Array.from(
    new Set(
      Array.from(
        { length: Math.min(6, items.length) },
        (_, index) =>
          items.length === 1
            ? 0
            : Math.round(
                (index * (items.length - 1)) /
                  (Math.min(6, items.length) - 1),
              ),
      ),
    ),
  );

  return (
    <Box sx={{ width: "100%", overflow: "hidden" }}>
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        role="img"
        aria-label="Monthly organizational payroll trend in US dollars"
        style={{
          width: "100%",
          height: "auto",
          display: "block",
        }}
      >
        {/* Horizontal grid lines and Y-axis labels */}
        {ticks.map((tick) => {
          const value = chartMax * tick;
          const y = getY(value);

          return (
            <g key={tick}>
              <line
                x1={PLOT.left}
                x2={CHART_WIDTH - PLOT.right}
                y1={y}
                y2={y}
                stroke="#E5EAF1"
                strokeWidth="1"
                strokeDasharray="4 4"
              />

              <text
                x={PLOT.left - 12}
                y={y + 4}
                textAnchor="end"
                fontSize="11"
                fill="#667085"
              >
                {formatCompactCurrency(value)}
              </text>
            </g>
          );
        })}

        {/* Area beneath the payroll trend */}
        <polygon
          points={areaPoints}
          fill="#2457C5"
          fillOpacity="0.10"
        />

        {/* Payroll trend line */}
        <polyline
          points={linePoints}
          fill="none"
          stroke="#2457C5"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Monthly data points */}
        {items.map((item, index) => (
          <g key={item.month}>
            <circle
              cx={getX(index)}
              cy={getY(values[index])}
              r="5"
              fill="#2457C5"
              stroke="#FFFFFF"
              strokeWidth="2"
            >
              <title>
                {formatMonth(item.month)} | Payroll:{" "}
                {formatCurrency(item.total_payroll_usd)} | Employees:{" "}
                {item.headcount.toLocaleString()} | Average salary:{" "}
                {formatCurrency(item.average_salary_usd)}
              </title>
            </circle>
          </g>
        ))}

        {/* Month labels */}
        {labelIndexes.map((index) => (
          <text
            key={index}
            x={getX(index)}
            y={CHART_HEIGHT - 18}
            textAnchor="middle"
            fontSize="11"
            fill="#667085"
          >
            {formatMonth(items[index].month)}
          </text>
        ))}
      </svg>
    </Box>
  );
}

function TrendMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <Box
      sx={{
        p: 2,
        borderRadius: 2,
        bgcolor: "background.default",
        minWidth: 0,
      }}
    >
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>

      <Typography
        variant="h6"
        fontWeight={750}
        sx={{ mt: 0.5, overflowWrap: "anywhere" }}
      >
        {value}
      </Typography>
    </Box>
  );
}

export function PayrollTrendsSection() {
  const [months, setMonths] = useState(12);
  const [country, setCountry] = useState("");
  const [department, setDepartment] = useState("");

  // Load available country and department filter options.
  const filtersQuery = useQuery({
    queryKey: ["employee-filters"],
    queryFn: ({ signal }) => employeeApi.getFilters(signal),
  });

  // Fetch payroll trends whenever the period or filters change.
  const trendQuery = useQuery({
    queryKey: [
      "analytics",
      "payroll-trends",
      months,
      country,
      department,
    ],
    queryFn: ({ signal }) =>
      analyticsApi.getPayrollTrends(months, signal, {
        country: country || undefined,
        department: department || undefined,
      }),
  });

  const items = trendQuery.data?.items ?? [];
  const latest = items[items.length - 1];

  return (
    <Paper
      variant="outlined"
      sx={{
        p: { xs: 2, md: 2.5 },
        borderRadius: 3,
      }}
    >
      {/* Chart heading and filters */}
      <Stack
        direction={{ xs: "column", sm: "row" }}
        alignItems={{ xs: "flex-start", sm: "center" }}
        justifyContent="space-between"
        spacing={2}
        sx={{ mb: 2.5 }}
      >
        <Box>
          <Typography variant="h6">
            Historical Payroll Trends
          </Typography>

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mt: 0.5 }}
          >
            Track how organizational compensation changes over time.
          </Typography>
        </Box>

        {/* Country, department and reporting period selectors */}
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1.5}
          sx={{ width: { xs: "100%", sm: "auto" } }}
        >
          {/* Country filter */}
          <FormControl size="small" sx={{ minWidth: 145 }}>
            <InputLabel id="trend-country-label">
              Country
            </InputLabel>

            <Select
              labelId="trend-country-label"
              value={country}
              label="Country"
              onChange={(event) => setCountry(event.target.value)}
            >
              <MenuItem value="">All countries</MenuItem>

              {(filtersQuery.data?.countries ?? []).map((value) => (
                <MenuItem key={value} value={value}>
                  {value}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Department filter */}
          <FormControl size="small" sx={{ minWidth: 155 }}>
            <InputLabel id="trend-department-label">
              Department
            </InputLabel>

            <Select
              labelId="trend-department-label"
              value={department}
              label="Department"
              onChange={(event) => setDepartment(event.target.value)}
            >
              <MenuItem value="">All departments</MenuItem>

              {(filtersQuery.data?.departments ?? []).map((value) => (
                <MenuItem key={value} value={value}>
                  {value}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Reporting period filter */}
          <FormControl size="small" sx={{ minWidth: 155 }}>
            <InputLabel id="payroll-trend-period">
              Reporting period
            </InputLabel>

            <Select
              labelId="payroll-trend-period"
              value={months}
              label="Reporting period"
              onChange={(event) =>
                setMonths(Number(event.target.value))
              }
            >
              <MenuItem value={3}>Last 3 months</MenuItem>
              <MenuItem value={6}>Last 6 months</MenuItem>
              <MenuItem value={12}>Last 12 months</MenuItem>
              <MenuItem value={24}>Last 24 months</MenuItem>
            </Select>
          </FormControl>
        </Stack>
      </Stack>

      {/* Filter loading or error state */}
      {filtersQuery.isError && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Country and department options could not be loaded.
          You can still view organization-wide payroll trends.
        </Alert>
      )}

      {/* Payroll chart loading state */}
      {trendQuery.isLoading ? (
        <Box
          sx={{
            py: 6,
            display: "grid",
            placeItems: "center",
          }}
        >
          <CircularProgress />

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mt: 1.5 }}
          >
            Loading payroll trends...
          </Typography>
        </Box>
      ) : trendQuery.isError ? (
        <Alert
          severity="error"
          action={
            <Box
              component="button"
              onClick={() => trendQuery.refetch()}
              sx={{
                border: 0,
                bgcolor: "transparent",
                color: "inherit",
                cursor: "pointer",
                fontWeight: 700,
              }}
            >
              Retry
            </Box>
          }
        >
          {trendQuery.error instanceof Error
            ? trendQuery.error.message
            : "Unable to load historical payroll data."}
        </Alert>
      ) : items.length === 0 ? (
        <Alert severity="info">
          There are no salary records available for this reporting period.
        </Alert>
      ) : (
        <Stack spacing={2.5}>
          {/* Latest month summary */}
          {latest && (
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: "1fr",
                  sm: "repeat(3, minmax(0, 1fr))",
                },
                gap: 1.5,
              }}
            >
              <TrendMetric
                label="Latest monthly payroll"
                value={formatCurrency(latest.total_payroll_usd)}
              />

              <TrendMetric
                label="Employees with salary records"
                value={latest.headcount.toLocaleString()}
              />

              <TrendMetric
                label="Latest average salary"
                value={formatCurrency(latest.average_salary_usd)}
              />
            </Box>
          )}

          {/* Payroll line chart */}
          <Box>
            <Typography
              variant="body2"
              fontWeight={650}
              sx={{ mb: 1 }}
            >
              Monthly total payroll (USD)
            </Typography>

            <PayrollLineChart items={items} />
          </Box>

          {/* Reporting methodology */}
          {trendQuery.data?.methodology_note && (
            <Alert severity="info">
              <Typography variant="body2">
                <strong>Reporting methodology:</strong>{" "}
                {trendQuery.data.methodology_note}
              </Typography>
            </Alert>
          )}
        </Stack>
      )}
    </Paper>
  );
}
