
import {
  AppBar,
  Box,
  Toolbar,
  Typography,
} from "@mui/material";

export function Header() {
  return (
    <AppBar
      position="fixed"
      elevation={0}
      color="inherit"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        borderBottom: 1,
        borderColor: "divider",
      }}
    >
      <Toolbar
        sx={{
          minHeight: "64px",
          px: { xs: 2, md: 3 },
        }}
      >
        <Typography
          variant="h6"
          color="primary"
          fontWeight={800}
          sx={{ letterSpacing: 1 }}
        >
          ACME
        </Typography>

        <Box
          sx={{
            width: 1,
            height: 25,
            bgcolor: "divider",
            mx: 2,
          }}
        />

        <Typography
          variant="body1"
          fontWeight={600}
        >
          Salary Management
        </Typography>

        <Box sx={{ flexGrow: 1 }} />

        <Typography
          variant="body2"
          color="text.secondary"
        >
          HR Manager
        </Typography>
      </Toolbar>
    </AppBar>
  );
}
