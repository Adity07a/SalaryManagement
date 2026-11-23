
import {
  Paper,
  Stack,
  Typography,
} from "@mui/material";

export function EmployeesPage() {
  return (
    <Stack spacing={3}>
      <Stack spacing={0.5}>
        <Typography variant="h4">
          Employees
        </Typography>

        <Typography color="text.secondary">
          Manage employee information, employment
          details and annual salaries.
        </Typography>
      </Stack>

      <Paper
        variant="outlined"
        sx={{ p: 3, borderRadius: 3 }}
      >
        <Typography variant="h6">
          Employee Directory
        </Typography>

        <Typography
          color="text.secondary"
          variant="body2"
          sx={{ mt: 1 }}
        >
          Employee records will be displayed in the
          server-paginated employee directory.
        </Typography>
      </Paper>
    </Stack>
  );
}
