
import { Box } from "@mui/material";
import { Outlet } from "react-router-dom";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

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
          pt: "68px",
        }}
      >
        <Box
          sx={{
            width: "100%",
            maxWidth: 1800,
            mx: "auto",
            px: { xs: 2, md: 3 },
            py: { xs: 2, md: 2.5 },
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
