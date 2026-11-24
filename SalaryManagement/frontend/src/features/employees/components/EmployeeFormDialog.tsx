
import { useEffect, useState, type FormEvent } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import type {
  CreateEmployeePayload,
  Employee,
  EmployeeFields,
  UpdateEmployeePayload,
} from "../../../api/types";

interface EmployeeFormDialogProps {
  open: boolean;
  mode: "create" | "edit";
  employee?: Employee | null;
  isSubmitting: boolean;
  error?: string | null;
  onClose: () => void;
  onSubmit: (
    payload: CreateEmployeePayload | UpdateEmployeePayload,
  ) => void;
}

const CURRENCIES = [
  "USD",
  "INR",
  "GBP",
  "CAD",
  "EUR",
  "AUD",
  "SGD",
  "JPY",
];

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

const EMPTY_FIELDS: EmployeeFields = {
  full_name: "",
  email: "",
  job_title: "",
  department: "",
  country: "IN",
  employment_type: "full_time",
  hire_date: today(),
};

export function EmployeeFormDialog({
  open,
  mode,
  employee,
  isSubmitting,
  error,
  onClose,
  onSubmit,
}: EmployeeFormDialogProps) {
  const [fields, setFields] = useState<EmployeeFields>(EMPTY_FIELDS);
  const [salaryAmount, setSalaryAmount] = useState("");
  const [salaryCurrency, setSalaryCurrency] = useState("INR");
  const [salaryEffectiveFrom, setSalaryEffectiveFrom] = useState(today());

  useEffect(() => {
    if (!open) return;

    if (mode === "edit" && employee) {
      setFields({
        full_name: employee.full_name,
        email: employee.email,
        job_title: employee.job_title,
        department: employee.department,
        country: employee.country,
        employment_type: employee.employment_type,
        hire_date: employee.hire_date,
      });
    } else {
      setFields({ ...EMPTY_FIELDS, hire_date: today() });
      setSalaryAmount("");
      setSalaryCurrency("INR");
      setSalaryEffectiveFrom(today());
    }
  }, [open, mode, employee]);

  const updateField = (field: keyof EmployeeFields, value: string) => {
    setFields((current) => ({
      ...current,
      [field]: value,
    }));

    if (field === "hire_date" && mode === "create") {
      setSalaryEffectiveFrom(value);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (mode === "create") {
      const payload: CreateEmployeePayload = {
        ...fields,
        initial_salary: {
          amount: salaryAmount,
          currency: salaryCurrency,
          effective_from: salaryEffectiveFrom,
        },
      };

      onSubmit(payload);
      return;
    }

    onSubmit(fields);
  };

  const invalidInitialSalaryDate =
    salaryEffectiveFrom < fields.hire_date;

  const invalidSalary =
    !salaryAmount ||
    !Number.isFinite(Number(salaryAmount)) ||
    Number(salaryAmount) <= 0;

  const submitDisabled =
    isSubmitting ||
    !fields.full_name.trim() ||
    !fields.email.trim() ||
    !fields.job_title.trim() ||
    !fields.department.trim() ||
    !/^[A-Z]{2}$/.test(fields.country) ||
    !fields.employment_type.trim() ||
    !fields.hire_date ||
    (mode === "create" &&
      (invalidSalary ||
        !salaryEffectiveFrom ||
        invalidInitialSalaryDate));

  return (
    <Dialog
      open={open}
      onClose={isSubmitting ? undefined : onClose}
      fullWidth
      maxWidth="md"
      scroll="paper"
    >
      <Box component="form" onSubmit={handleSubmit}>
        <DialogTitle>
          {mode === "create" ? "Add Employee" : "Edit Employee"}

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mt: 0.5 }}
          >
            {mode === "create"
              ? "Enter employee details and their initial salary."
              : "Update the employee's personal and employment information."}
          </Typography>
        </DialogTitle>

        <DialogContent dividers>
          <Stack spacing={2.5}>
            {error && <Alert severity="error">{error}</Alert>}

            <Typography variant="subtitle2">
              Personal and employment details
            </Typography>

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
              <TextField
                label="Full name"
                value={fields.full_name}
                onChange={(event) =>
                  updateField("full_name", event.target.value)
                }
                required
                fullWidth
                autoFocus
              />

              <TextField
                label="Email address"
                type="email"
                value={fields.email}
                onChange={(event) =>
                  updateField("email", event.target.value)
                }
                required
                fullWidth
              />

              <TextField
                label="Job title"
                value={fields.job_title}
                onChange={(event) =>
                  updateField("job_title", event.target.value)
                }
                required
                fullWidth
              />

              <TextField
                label="Department"
                value={fields.department}
                onChange={(event) =>
                  updateField("department", event.target.value)
                }
                required
                fullWidth
              />

              <TextField
                label="Country code"
                value={fields.country}
                onChange={(event) =>
                  updateField(
                    "country",
                    event.target.value.toUpperCase(),
                  )
                }
                required
                fullWidth
                helperText="Use a two-letter ISO country code, e.g. IN, US, GB."
                slotProps={{
                  htmlInput: {
                    maxLength: 2,
                  },
                }}
              />

              <TextField
                label="Employment type"
                value={fields.employment_type}
                onChange={(event) =>
                  updateField("employment_type", event.target.value)
                }
                required
                fullWidth
                helperText="Example: full_time"
              />

              <TextField
                label="Hire date"
                type="date"
                value={fields.hire_date}
                onChange={(event) =>
                  updateField("hire_date", event.target.value)
                }
                required
                fullWidth
                slotProps={{
                  inputLabel: { shrink: true },
                }}
              />
            </Box>

            {mode === "create" && (
              <>
                <Typography variant="subtitle2" sx={{ pt: 1 }}>
                  Initial salary
                </Typography>

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
                  <TextField
                    label="Salary amount"
                    type="number"
                    value={salaryAmount}
                    onChange={(event) =>
                      setSalaryAmount(event.target.value)
                    }
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
                    onChange={(event) =>
                      setSalaryCurrency(event.target.value)
                    }
                    required
                    fullWidth
                  >
                    {CURRENCIES.map((currency) => (
                      <MenuItem key={currency} value={currency}>
                        {currency}
                      </MenuItem>
                    ))}
                  </TextField>

                  <TextField
                    label="Salary effective from"
                    type="date"
                    value={salaryEffectiveFrom}
                    onChange={(event) =>
                      setSalaryEffectiveFrom(event.target.value)
                    }
                    required
                    fullWidth
                    slotProps={{
                      inputLabel: { shrink: true },
                      htmlInput: {
                        min: fields.hire_date,
                      },
                    }}
                  />
                </Box>

                {invalidInitialSalaryDate && (
                  <Alert severity="warning">
                    The initial salary effective date cannot be earlier
                    than the employee's hire date.
                  </Alert>
                )}

                <Alert severity="info">
                  The selected currency must have an exchange rate
                  configured in the database.
                </Alert>
              </>
            )}
          </Stack>
        </DialogContent>

        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button
            onClick={onClose}
            color="inherit"
            disabled={isSubmitting}
          >
            Cancel
          </Button>

          <Button
            type="submit"
            variant="contained"
            disabled={submitDisabled}
            startIcon={
              isSubmitting ? (
                <CircularProgress size={16} color="inherit" />
              ) : undefined
            }
          >
            {isSubmitting
              ? "Saving..."
              : mode === "create"
                ? "Create Employee"
                : "Save Changes"}
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  );
}
