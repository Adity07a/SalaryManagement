
import {
  Paper,
  Stack,
  Typography,
} from "@mui/material";

export function InsightsPage() {
  return (
    <Stack spacing={3}>
      <Stack spacing={0.5}>
        <Typography variant="h4">
          Salary Insights
        </Typography>

        <Typography color="text.secondary">
          Understand organizational payroll,
          salary distribution and compensation patterns.
        </Typography>
      </Stack>

      <Paper
        variant="outlined"
        sx={{ p: 3, borderRadius: 3 }}
      >
        <Typography variant="h6">
          Organizational Compensation
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 1 }}
        >
          Salary analytics and organizational
          statistics will be displayed here.
        </Typography>
      </Paper>
    </Stack>
  );
}
