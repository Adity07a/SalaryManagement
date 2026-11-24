
import { useState, type FormEvent } from "react";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import AddIcon from "@mui/icons-material/Add";
import AccountBalanceWalletOutlinedIcon from "@mui/icons-material/AccountBalanceWalletOutlined";
import WorkOutlineIcon from "@mui/icons-material/WorkOutline";
import { Link as RouterLink, useParams } from "react-router-dom";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { employeeApi } from "../../../api/employees";
import type { AddSalaryPayload, SalaryRecord } from "../../../api/types";

const SUPPORTED_CURRENCIES = [
  "USD",
  "INR",
  "GBP",
  "CAD",
  "EUR",
  "AUD",
  "SGD",
  "JPY",
];

function formatCurrency(value: string, currency: string): string {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return `${value} ${currency}`;
  }

  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${value} ${currency}`;
  }
}

function formatDate(value: string): string {
  if (!value) return "—";

  const [year, month, day] = value.split("T")[0].split("-").map(Number);

  if (!year || !month || !day) return value;

  return new Intl.DateTimeFormat("en", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(year, month - 1, day));
}

function getInitials(fullName: string): string {
  return fullName
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function DetailItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <Stack spacing={0.5}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>

      <Typography variant="body2" fontWeight={600}>
        {value || "—"}
      </Typography>
    </Stack>
  );
}

function getSalarySortDate(salary: SalaryRecord): number {
  return new Date(salary.effective_from).getTime();
}

export function EmployeeDetailPage() {
  const { employeeId } = useParams<{ employeeId: string }>();
  const queryClient = useQueryClient();

  const id = Number(employeeId);
  const validId = Number.isInteger(id) && id > 0;

  const [salaryDialogOpen, setSalaryDialogOpen] = useState(false);
  const [salaryAmount, setSalaryAmount] = useState("");
  const [salaryCurrency, setSalaryCurrency] = useState("USD");
  const [effectiveFrom, setEffectiveFrom] = useState("");

  const employeeQuery = useQuery({
    queryKey: ["employee", id],
    queryFn: ({ signal }) => employeeApi.getById(id, signal),
    enabled: validId,
  });

  const addSalaryMutation = useMutation({
    mutationFn: (payload: AddSalaryPayload) =>
      employeeApi.addSalary(id, payload),

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["employee", id],
        }),
        queryClient.invalidateQueries({
          queryKey: ["employees"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["analytics"],
        }),
      ]);

      setSalaryDialogOpen(false);
      setSalaryAmount("");
      setSalaryCurrency("USD");
      setEffectiveFrom("");
    },
  });

  const employee = employeeQuery.data;

  const salaryHistory = [...(employee?.salary_history ?? [])].sort(
    (a, b) => getSalarySortDate(b) - getSalarySortDate(a),
  );

  const openSalaryDialog = () => {
    addSalaryMutation.reset();
    setSalaryAmount("");
    setSalaryCurrency("USD");
    setEffectiveFrom(
      new Date().toISOString().slice(0, 10),
    );
    setSalaryDialogOpen(true);
  };

  const closeSalaryDialog = () => {
    if (addSalaryMutation.isPending) return;

    setSalaryDialogOpen(false);
    addSalaryMutation.reset();
  };

  const handleAddSalary = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!employee) return;

    const amount = Number(salaryAmount);

    if (!Number.isFinite(amount) || amount <= 0) {
      return;
    }

    if (!effectiveFrom || effectiveFrom < employee.hire_date) {
      return;
    }

    addSalaryMutation.mutate({
      amount: salaryAmount,
      currency: salaryCurrency,
      effective_from: effectiveFrom,
    });
  };

  if (!validId) {
    return (
      <Alert severity="error">
        Invalid employee ID. Return to the employee directory and select
        a valid employee.
      </Alert>
    );
  }

  if (employeeQuery.isLoading) {
    return (
      <Box
        sx={{
          minHeight: 300,
          display: "grid",
          placeItems: "center",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (employeeQuery.isError || !employee) {
    return (
      <Stack spacing={2}>
        <Alert severity="error">
          {employeeQuery.error instanceof Error
            ? employeeQuery.error.message
            : "Unable to load employee details."}
        </Alert>

        <Button
          component={RouterLink}
          to="/employees"
          startIcon={<ArrowBackIcon />}
          sx={{ alignSelf: "flex-start" }}
        >
          Back to employees
        </Button>
      </Stack>
    );
  }

  return (
    <Stack spacing={2.5}>
      {/* Navigation and page actions */}
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
      >
        <Button
          component={RouterLink}
          to="/employees"
          startIcon={<ArrowBackIcon />}
          color="inherit"
        >
          Back to employees
        </Button>

        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={openSalaryDialog}
        >
          Add salary record
        </Button>
      </Stack>

      {/* Employee heading */}
      <Paper variant="outlined" sx={{ p: 3, borderRadius: 3 }}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          alignItems={{ xs: "flex-start", sm: "center" }}
          spacing={2}
        >
          <Avatar
            sx={{
              width: 64,
              height: 64,
              bgcolor: "primary.light",
              color: "primary.dark",
              fontSize: 21,
              fontWeight: 750,
            }}
          >
            {getInitials(employee.full_name)}
          </Avatar>

          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="h5">
              {employee.full_name}
            </Typography>

            <Typography color="text.secondary" sx={{ mt: 0.25 }}>
              {employee.job_title}
            </Typography>

            <Stack
              direction="row"
              spacing={1}
              flexWrap="wrap"
              sx={{ mt: 1 }}
            >
              <Chip
                size="small"
                label={employee.department}
                variant="outlined"
              />

              <Chip
                size="small"
                label={employee.country}
                variant="outlined"
              />

              <Chip
                size="small"
                label={employee.employment_type.replaceAll("_", " ")}
                color="success"
                variant="outlined"
              />
            </Stack>
          </Box>

          <Box>
            <Typography variant="caption" color="text.secondary">
              Employee ID
            </Typography>
            <Typography fontWeight={700}>
              #{employee.id}
            </Typography>
          </Box>
        </Stack>
      </Paper>

      {/* Current salary */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            sm: "repeat(2, minmax(0, 1fr))",
          },
          gap: 2,
        }}
      >
        <Paper variant="outlined" sx={{ p: 2.5, borderRadius: 3 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <AccountBalanceWalletOutlinedIcon color="primary" />
            <Typography variant="body2" color="text.secondary">
              Current salary
            </Typography>
          </Stack>

          <Typography variant="h5" fontWeight={750} sx={{ mt: 1.5 }}>
            {employee.current_salary
              ? formatCurrency(
                  employee.current_salary.amount,
                  employee.current_salary.currency,
                )
              : "Not available"}
          </Typography>

          {employee.current_salary && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 0.5 }}
            >
              {formatCurrency(
                employee.current_salary.amount_usd,
                "USD",
              )}{" "}
              equivalent
            </Typography>
          )}
        </Paper>

        <Paper variant="outlined" sx={{ p: 2.5, borderRadius: 3 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <WorkOutlineIcon color="primary" />
            <Typography variant="body2" color="text.secondary">
              Employment information
            </Typography>
          </Stack>

          <Typography variant="h5" fontWeight={750} sx={{ mt: 1.5 }}>
            {formatDate(employee.hire_date)}
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Hire date
          </Typography>
        </Paper>
      </Box>

      {/* Employee profile information */}
      <Paper variant="outlined" sx={{ p: 2.5, borderRadius: 3 }}>
        <Typography variant="h6" sx={{ mb: 2.5 }}>
          Employee Information
        </Typography>

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, minmax(0, 1fr))",
              lg: "repeat(3, minmax(0, 1fr))",
            },
            gap: 3,
          }}
        >
          <DetailItem label="Full name" value={employee.full_name} />
          <DetailItem label="Email address" value={employee.email} />
          <DetailItem label="Job title" value={employee.job_title} />
          <DetailItem label="Department" value={employee.department} />
          <DetailItem label="Country" value={employee.country} />
          <DetailItem
            label="Employment type"
            value={employee.employment_type.replaceAll("_", " ")}
          />
          <DetailItem
            label="Hire date"
            value={formatDate(employee.hire_date)}
          />
          <DetailItem
            label="Employee record created"
            value={formatDate(employee.created_at)}
          />
          <DetailItem
            label="Last updated"
            value={formatDate(employee.updated_at)}
          />
        </Box>
      </Paper>

      {/* Salary history */}
      <Paper
        variant="outlined"
        sx={{ borderRadius: 3, overflow: "hidden" }}
      >
        <Box sx={{ p: 2.5 }}>
          <Typography variant="h6">Salary History</Typography>

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mt: 0.5 }}
          >
            Historical compensation records, ordered by effective date.
          </Typography>
        </Box>

        <Divider />

        {salaryHistory.length === 0 ? (
          <Box sx={{ p: 4, textAlign: "center" }}>
            <Typography fontWeight={650}>
              No salary records found
            </Typography>

            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 0.5 }}
            >
              Add a salary record to start tracking this employee's
              compensation history.
            </Typography>
          </Box>
        ) : (
          <TableContainer>
            <Table sx={{ minWidth: 650 }}>
              <TableHead>
                <TableRow sx={{ bgcolor: "background.default" }}>
                  <TableCell>Effective date</TableCell>
                  <TableCell align="right">Salary</TableCell>
                  <TableCell align="right">USD equivalent</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {salaryHistory.map((salary, index) => (
                  <TableRow key={salary.id} hover>
                    <TableCell>
                      {formatDate(salary.effective_from)}
                    </TableCell>

                    <TableCell align="right">
                      {formatCurrency(salary.amount, salary.currency)}
                    </TableCell>

                    <TableCell align="right">
                      {formatCurrency(salary.amount_usd, "USD")}
                    </TableCell>

                    <TableCell>
                      {index === 0 ? (
                        <Chip
                          label="Latest"
                          size="small"
                          color="success"
                          variant="outlined"
                        />
                      ) : (
                        <Chip
                          label="Historical"
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Add salary dialog */}
      <Dialog
        open={salaryDialogOpen}
        onClose={closeSalaryDialog}
        fullWidth
        maxWidth="sm"
      >
        <Box component="form" onSubmit={handleAddSalary}>
          <DialogTitle>Add Salary Record</DialogTitle>

          <DialogContent>
            <Stack spacing={2.5} sx={{ pt: 1 }}>
              <Alert severity="info">
                Salary records are append-only. Adding a new record
                preserves the employee's previous salary history.
              </Alert>

              <TextField
                label="Salary amount"
                type="number"
                value={salaryAmount}
                onChange={(event) => setSalaryAmount(event.target.value)}
                required
                fullWidth
                slotProps={{
                  htmlInput: {
                    min: "0.01",
                    step: "0.01",
                  },
                }}
              />

              <TextField
                select
                label="Currency"
                value={salaryCurrency}
                onChange={(event) => setSalaryCurrency(event.target.value)}
                fullWidth
                required
              >
                {SUPPORTED_CURRENCIES.map((currency) => (
                  <MenuItem key={currency} value={currency}>
                    {currency}
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                label="Effective from"
                type="date"
                value={effectiveFrom}
                onChange={(event) => setEffectiveFrom(event.target.value)}
                required
                fullWidth
                slotProps={{
                  inputLabel: { shrink: true },
                  htmlInput: {
                    min: employee.hire_date,
                  },
                }}
              />

              {effectiveFrom && effectiveFrom < employee.hire_date && (
                <Alert severity="warning">
                  The effective date cannot be earlier than the employee's
                  hire date.
                </Alert>
              )}

              {addSalaryMutation.isError && (
                <Alert severity="error">
                  {addSalaryMutation.error instanceof Error
                    ? addSalaryMutation.error.message
                    : "Unable to add salary record."}
                </Alert>
              )}
            </Stack>
          </DialogContent>

          <DialogActions sx={{ px: 3, pb: 2.5 }}>
            <Button
              onClick={closeSalaryDialog}
              color="inherit"
              disabled={addSalaryMutation.isPending}
            >
              Cancel
            </Button>

            <Button
              type="submit"
              variant="contained"
              disabled={
                addSalaryMutation.isPending ||
                !salaryAmount ||
                Number(salaryAmount) <= 0 ||
                !effectiveFrom ||
                effectiveFrom < employee.hire_date
              }
              startIcon={
                addSalaryMutation.isPending ? (
                  <CircularProgress size={16} color="inherit" />
                ) : (
                  <AddIcon />
                )
              }
            >
              {addSalaryMutation.isPending
                ? "Saving..."
                : "Save Salary"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </Stack>
  );
}
