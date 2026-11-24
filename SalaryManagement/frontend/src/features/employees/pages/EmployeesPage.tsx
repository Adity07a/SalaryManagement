
import { useState, type ChangeEvent } from "react";

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
  DialogContentText,
  DialogTitle,
  FormControl,
  IconButton,
  InputAdornment,
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
  TablePagination,
  TableRow,
  TableSortLabel,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";

import AddIcon from "@mui/icons-material/Add";
import ClearIcon from "@mui/icons-material/Clear";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import PeopleOutlineIcon from "@mui/icons-material/PeopleOutline";
import RefreshIcon from "@mui/icons-material/Refresh";
import SearchIcon from "@mui/icons-material/Search";

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { Link as RouterLink } from "react-router-dom";

import { employeeApi } from "../../../api/employees";

import type {
  CreateEmployeePayload,
  Employee,
  UpdateEmployeePayload,
} from "../../../api/types";

import { EmployeeFormDialog } from "../components/EmployeeFormDialog";

type SortField = "full_name" | "department" | "country" | "hire_date";

interface SortConfig {
  field: SortField;
  order: "asc" | "desc";
}

type SaveEmployeeCommand =
  | {
      mode: "create";
      payload: CreateEmployeePayload;
    }
  | {
      mode: "update";
      id: number;
      payload: UpdateEmployeePayload;
    };

const DEFAULT_PAGE_SIZE = 25;

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
  const datePart = value.split("T")[0];
  const [year, month, day] = datePart.split("-").map(Number);

  if (!year || !month || !day) {
    return value;
  }

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

function SortableHeader({
  label,
  field,
  sort,
  onSort,
}: {
  label: string;
  field: SortField;
  sort: SortConfig;
  onSort: (field: SortField) => void;
}) {
  return (
    <TableCell
      sortDirection={sort.field === field ? sort.order : false}
    >
      <TableSortLabel
        active={sort.field === field}
        direction={sort.field === field ? sort.order : "asc"}
        onClick={() => onSort(field)}
      >
        {label}
      </TableSortLabel>
    </TableCell>
  );
}

export function EmployeesPage() {
  const queryClient = useQueryClient();

  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const [search, setSearch] = useState("");
  const [country, setCountry] = useState("");
  const [department, setDepartment] = useState("");
  const [jobTitle, setJobTitle] = useState("");

  const [sort, setSort] = useState<SortConfig>({
    field: "full_name",
    order: "asc",
  });

  const [formOpen, setFormOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(
    null,
  );
  const [deletingEmployee, setDeletingEmployee] = useState<Employee | null>(
    null,
  );

  const filtersQuery = useQuery({
    queryKey: ["employee-filters"],
    queryFn: ({ signal }) => employeeApi.getFilters(signal),
  });

  const employeesQuery = useQuery({
    queryKey: [
      "employees",
      page,
      pageSize,
      search,
      country,
      department,
      jobTitle,
      sort.field,
      sort.order,
    ],
    queryFn: ({ signal }) =>
      employeeApi.list(
        {
          page: page + 1,
          page_size: pageSize,
          search: search.trim() || undefined,
          country: country || undefined,
          department: department || undefined,
          job_title: jobTitle || undefined,
          sort_by: sort.field,
          sort_order: sort.order,
        },
        signal,
      ),
    placeholderData: keepPreviousData,
  });

  const saveEmployeeMutation = useMutation({
    mutationFn: (command: SaveEmployeeCommand) => {
      if (command.mode === "create") {
        return employeeApi.create(command.payload);
      }

      return employeeApi.update(command.id, command.payload);
    },

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["employees"] }),
        queryClient.invalidateQueries({ queryKey: ["employee-filters"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics"] }),
      ]);

      setPage(0);
      setFormOpen(false);
      setEditingEmployee(null);
    },
  });

  const deleteEmployeeMutation = useMutation({
    mutationFn: (id: number) => employeeApi.remove(id),

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["employees"] }),
        queryClient.invalidateQueries({ queryKey: ["employee-filters"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics"] }),
      ]);

      setPage(0);
      setDeletingEmployee(null);
    },
  });

  const employees = employeesQuery.data?.items ?? [];
  const total = employeesQuery.data?.total ?? 0;

  const hasActiveFilters = Boolean(
    search.trim() || country || department || jobTitle,
  );

  const openCreateDialog = () => {
    saveEmployeeMutation.reset();
    setEditingEmployee(null);
    setFormOpen(true);
  };

  const openEditDialog = (employee: Employee) => {
    saveEmployeeMutation.reset();
    setEditingEmployee(employee);
    setFormOpen(true);
  };

  const closeFormDialog = () => {
    if (saveEmployeeMutation.isPending) return;

    setFormOpen(false);
    setEditingEmployee(null);
    saveEmployeeMutation.reset();
  };

  const handleEmployeeSubmit = (
    payload: CreateEmployeePayload | UpdateEmployeePayload,
  ) => {
    if (editingEmployee) {
      saveEmployeeMutation.mutate({
        mode: "update",
        id: editingEmployee.id,
        payload: payload as UpdateEmployeePayload,
      });
    } else {
      saveEmployeeMutation.mutate({
        mode: "create",
        payload: payload as CreateEmployeePayload,
      });
    }
  };

  const handleSort = (field: SortField) => {
    setSort((current) => ({
      field,
      order:
        current.field === field && current.order === "asc"
          ? "desc"
          : "asc",
    }));

    setPage(0);
  };

  const resetFilters = () => {
    setSearch("");
    setCountry("");
    setDepartment("");
    setJobTitle("");
    setPage(0);
  };

  const handlePageChange = (_event: unknown, nextPage: number) => {
    setPage(nextPage);
  };

  const handlePageSizeChange = (
    event: ChangeEvent<HTMLInputElement>,
  ) => {
    setPageSize(Number(event.target.value));
    setPage(0);
  };

  const confirmDelete = () => {
    if (!deletingEmployee) return;

    deleteEmployeeMutation.mutate(deletingEmployee.id);
  };

  return (
    <Stack spacing={2.5}>
      {/* Page heading */}
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={1.5}
      >
        <Box>
          <Typography variant="h4">Employees</Typography>

          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            Manage employee information, employment details and salaries.
          </Typography>
        </Box>

        <Stack direction="row" spacing={1.5} alignItems="center">
          <Chip
            icon={<PeopleOutlineIcon />}
            label={`${total.toLocaleString()} employees`}
            color="primary"
            variant="outlined"
          />

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={openCreateDialog}
          >
            Add employee
          </Button>
        </Stack>
      </Stack>

      {/* Global action errors */}
      {deleteEmployeeMutation.isError && (
        <Alert
          severity="error"
          onClose={() => deleteEmployeeMutation.reset()}
        >
          {deleteEmployeeMutation.error instanceof Error
            ? deleteEmployeeMutation.error.message
            : "Unable to delete employee."}
        </Alert>
      )}

      {/* Filters */}
      <Paper
        variant="outlined"
        sx={{ p: { xs: 2, md: 2.5 }, borderRadius: 3 }}
      >
        <Stack spacing={2}>
          <Stack
            direction={{ xs: "column", md: "row" }}
            spacing={2}
            alignItems={{ md: "center" }}
          >
            <TextField
              fullWidth
              size="small"
              label="Search employees"
              placeholder="Search by name or email"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(0);
              }}
              sx={{ flex: 1 }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: search ? (
                    <InputAdornment position="end">
                      <IconButton
                        size="small"
                        aria-label="Clear search"
                        onClick={() => {
                          setSearch("");
                          setPage(0);
                        }}
                      >
                        <ClearIcon fontSize="small" />
                      </IconButton>
                    </InputAdornment>
                  ) : undefined,
                },
              }}
            />

            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel id="country-filter-label">Country</InputLabel>
              <Select
                labelId="country-filter-label"
                value={country}
                label="Country"
                onChange={(event) => {
                  setCountry(event.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="">All countries</MenuItem>
                {(filtersQuery.data?.countries ?? []).map((value) => (
                  <MenuItem key={value} value={value}>
                    {value}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 170 }}>
              <InputLabel id="department-filter-label">
                Department
              </InputLabel>
              <Select
                labelId="department-filter-label"
                value={department}
                label="Department"
                onChange={(event) => {
                  setDepartment(event.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="">All departments</MenuItem>
                {(filtersQuery.data?.departments ?? []).map((value) => (
                  <MenuItem key={value} value={value}>
                    {value}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 170 }}>
              <InputLabel id="job-title-filter-label">
                Job title
              </InputLabel>
              <Select
                labelId="job-title-filter-label"
                value={jobTitle}
                label="Job title"
                onChange={(event) => {
                  setJobTitle(event.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="">All job titles</MenuItem>
                {(filtersQuery.data?.job_titles ?? []).map((value) => (
                  <MenuItem key={value} value={value}>
                    {value}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Button
              variant="text"
              color="inherit"
              startIcon={<RefreshIcon />}
              onClick={resetFilters}
              disabled={!hasActiveFilters}
              sx={{ whiteSpace: "nowrap" }}
            >
              Reset
            </Button>
          </Stack>

          {filtersQuery.isError && (
            <Alert severity="warning">
              Employee filter options could not be loaded. Search and
              the employee directory are still available.
            </Alert>
          )}

          {employeesQuery.isError && (
            <Alert
              severity="error"
              action={
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => employeesQuery.refetch()}
                >
                  Retry
                </Button>
              }
            >
              {employeesQuery.error instanceof Error
                ? employeesQuery.error.message
                : "Unable to load employees."}
            </Alert>
          )}
        </Stack>
      </Paper>

      {/* Employee table */}
      <Paper variant="outlined" sx={{ borderRadius: 3, overflow: "hidden" }}>
        <Box
          sx={{
            px: 2.5,
            py: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: 1,
            borderColor: "divider",
          }}
        >
          <Box>
            <Typography variant="h6">Employee Directory</Typography>

            <Typography variant="body2" color="text.secondary">
              Employee profiles and current salary information
            </Typography>
          </Box>

          {employeesQuery.isFetching && (
            <CircularProgress size={22} aria-label="Refreshing employees" />
          )}
        </Box>

        <TableContainer>
          <Table sx={{ minWidth: 1150 }} aria-label="Employee directory">
            <TableHead>
              <TableRow sx={{ bgcolor: "background.default" }}>
                <SortableHeader
                  label="Employee"
                  field="full_name"
                  sort={sort}
                  onSort={handleSort}
                />

                <TableCell>Job title</TableCell>

                <SortableHeader
                  label="Department"
                  field="department"
                  sort={sort}
                  onSort={handleSort}
                />

                <SortableHeader
                  label="Country"
                  field="country"
                  sort={sort}
                  onSort={handleSort}
                />

                <TableCell>Employment type</TableCell>

                <SortableHeader
                  label="Hire date"
                  field="hire_date"
                  sort={sort}
                  onSort={handleSort}
                />

                <TableCell align="right">Current salary</TableCell>

                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {employeesQuery.isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 7 }}>
                    <CircularProgress size={30} />
                    <Typography color="text.secondary" sx={{ mt: 1 }}>
                      Loading employees...
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : employees.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 7 }}>
                    <PeopleOutlineIcon
                      sx={{ fontSize: 42, color: "text.secondary" }}
                    />

                    <Typography variant="h6" sx={{ mt: 1 }}>
                      No employees found
                    </Typography>

                    <Typography color="text.secondary" variant="body2">
                      {hasActiveFilters
                        ? "Try changing your search or filters."
                        : "There are no employee records to display."}
                    </Typography>

                    {hasActiveFilters && (
                      <Button
                        size="small"
                        onClick={resetFilters}
                        sx={{ mt: 1 }}
                      >
                        Clear filters
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ) : (
                employees.map((employee) => (
                  <TableRow
                    key={employee.id}
                    hover
                    sx={{
                      "&:last-child td": { borderBottom: 0 },
                    }}
                  >
                    <TableCell>
                      <Stack direction="row" spacing={1.5} alignItems="center">
                        <Avatar
                          sx={{
                            width: 38,
                            height: 38,
                            bgcolor: "primary.light",
                            color: "primary.dark",
                            fontSize: 13,
                            fontWeight: 700,
                          }}
                        >
                          {getInitials(employee.full_name)}
                        </Avatar>

                        <Box sx={{ minWidth: 0 }}>
                          <Typography
                            component={RouterLink}
                            to={`/employees/${employee.id}`}
                            variant="body2"
                            fontWeight={650}
                            color="text.primary"
                            sx={{
                              textDecoration: "none",
                              "&:hover": {
                                color: "primary.main",
                                textDecoration: "underline",
                              },
                            }}
                          >
                            {employee.full_name}
                          </Typography>

                          <Typography
                            variant="caption"
                            color="text.secondary"
                          >
                            {employee.email}
                          </Typography>
                        </Box>
                      </Stack>
                    </TableCell>

                    <TableCell>{employee.job_title}</TableCell>
                    <TableCell>{employee.department}</TableCell>
                    <TableCell>{employee.country}</TableCell>

                    <TableCell>
                      <Chip
                        size="small"
                        variant="outlined"
                        label={employee.employment_type.replaceAll("_", " ")}
                      />
                    </TableCell>

                    <TableCell>{formatDate(employee.hire_date)}</TableCell>

                    <TableCell align="right">
                      {employee.current_salary ? (
                        <Stack spacing={0.25} alignItems="flex-end">
                          <Typography variant="body2" fontWeight={650}>
                            {formatCurrency(
                              employee.current_salary.amount,
                              employee.current_salary.currency,
                            )}
                          </Typography>

                          <Typography variant="caption" color="text.secondary">
                            {formatCurrency(
                              employee.current_salary.amount_usd,
                              "USD",
                            )}{" "}
                            equivalent
                          </Typography>
                        </Stack>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          Not available
                        </Typography>
                      )}
                    </TableCell>

                    <TableCell align="center">
                      <Stack
                        direction="row"
                        spacing={0.5}
                        justifyContent="center"
                      >
                        <Tooltip title="Edit employee">
                          <IconButton
                            size="small"
                            color="primary"
                            aria-label={`Edit ${employee.full_name}`}
                            onClick={() => openEditDialog(employee)}
                          >
                            <EditOutlinedIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>

                        <Tooltip title="Delete employee">
                          <IconButton
                            size="small"
                            color="error"
                            aria-label={`Delete ${employee.full_name}`}
                            onClick={() => {
                              deleteEmployeeMutation.reset();
                              setDeletingEmployee(employee);
                            }}
                          >
                            <DeleteOutlineIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={handlePageChange}
          rowsPerPage={pageSize}
          onRowsPerPageChange={handlePageSizeChange}
          rowsPerPageOptions={[10, 25, 50, 100]}
          labelRowsPerPage="Employees per page"
        />
      </Paper>

      {/* Create and edit dialog */}
      <EmployeeFormDialog
        open={formOpen}
        mode={editingEmployee ? "edit" : "create"}
        employee={editingEmployee}
        isSubmitting={saveEmployeeMutation.isPending}
        error={
          saveEmployeeMutation.isError
            ? saveEmployeeMutation.error.message
            : null
        }
        onClose={closeFormDialog}
        onSubmit={handleEmployeeSubmit}
      />

      {/* Permanent deletion confirmation */}
      <Dialog
        open={Boolean(deletingEmployee)}
        onClose={
          deleteEmployeeMutation.isPending
            ? undefined
            : () => setDeletingEmployee(null)
        }
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Delete employee?</DialogTitle>

        <DialogContent>
          <DialogContentText>
            You are about to permanently delete{" "}
            <strong>{deletingEmployee?.full_name}</strong>.

            <br />
            <br />

            This also deletes the employee's associated salary records.
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button
            color="inherit"
            onClick={() => setDeletingEmployee(null)}
            disabled={deleteEmployeeMutation.isPending}
          >
            Cancel
          </Button>

          <Button
            color="error"
            variant="contained"
            onClick={confirmDelete}
            disabled={deleteEmployeeMutation.isPending}
            startIcon={
              deleteEmployeeMutation.isPending ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <DeleteOutlineIcon />
              )
            }
          >
            {deleteEmployeeMutation.isPending
              ? "Deleting..."
              : "Delete permanently"}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
