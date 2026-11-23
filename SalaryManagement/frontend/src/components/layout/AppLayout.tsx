
import { Box } from "@mui/material";
import { Outlet } from "react-router-dom";

import { Header } from "./Header";
import {
  DRAWER_WIDTH,
  Sidebar,
} from "./Sidebar";

export function AppLayout() {
  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <Header />

      <Sidebar />

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          minWidth: 0,
          ml: `${DRAWER_WIDTH}px`,
          pt: "64px",
        }}
      >
        <Box
          sx={{
            maxWidth: 1600,
            mx: "auto",
            p: { xs: 2, md: 4 },
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
