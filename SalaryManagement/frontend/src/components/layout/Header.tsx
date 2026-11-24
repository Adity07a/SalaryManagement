
import {
  AppBar,
  Avatar,
  Box,
  Chip,
  Stack,
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
        bgcolor: "background.paper",
      }}
    >
      <Toolbar
        sx={{
          minHeight: "68px",
          px: { xs: 2, md: 3 },
        }}
      >
        <Stack direction="row" alignItems="center" spacing={2}>
          <Typography
            variant="h6"
            color="primary"
            fontWeight={850}
            sx={{
              letterSpacing: 1.2,
              fontSize: "1.35rem",
            }}
          >
            ACME
          </Typography>

          <Box
            sx={{
              width: "1px",
              height: 34,
              bgcolor: "divider",
              flexShrink: 0,
            }}
          />

          <Stack spacing={0}>
            <Typography
              variant="subtitle1"
              fontWeight={750}
              lineHeight={1.4}
            >
              Salary Management
            </Typography>

            <Typography
              variant="caption"
              color="text.secondary"
            >
              People & Compensation
            </Typography>
          </Stack>
        </Stack>

        <Box sx={{ flexGrow: 1 }} />

        <Stack
          direction="row"
          spacing={1.5}
          alignItems="center"
        >
          <Chip
            label="HR WORKSPACE"
            size="small"
            variant="outlined"
            sx={{
              display: { xs: "none", sm: "inline-flex" },
              borderColor: "divider",
              color: "text.secondary",
              fontWeight: 650,
              letterSpacing: 0.3,
            }}
          />

          <Avatar
            sx={{
              width: 36,
              height: 36,
              bgcolor: "primary.light",
              color: "primary.dark",
              fontSize: 13,
              fontWeight: 750,
            }}
          >
            HR
          </Avatar>

          <Stack spacing={0} sx={{ display: { xs: "none", sm: "flex" } }}>
            <Typography variant="body2" fontWeight={700}>
              HR Manager
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Administrator
            </Typography>
          </Stack>
        </Stack>
      </Toolbar>
    </AppBar>
  );
}
