
import {
  Paper,
  Stack,
  Typography,
} from "@mui/material";

import { useParams } from "react-router-dom";

export function EmployeeDetailPage() {
  const { employeeId } = useParams<{
    employeeId: string;
  }>();

  return (
    <Stack spacing={3}>
      <Stack spacing={0.5}>
        <Typography variant="h4">
          Employee Details
        </Typography>

        <Typography color="text.secondary">
          Employee ID: {employeeId}
        </Typography>
      </Stack>

      <Paper
        variant="outlined"
        sx={{ p: 3, borderRadius: 3 }}
      >
        <Typography variant="h6">
          Employee Profile
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 1 }}
        >
          Employee information and salary history
          will be loaded from the employee detail API.
        </Typography>
      </Paper>
    </Stack>
  );
}
