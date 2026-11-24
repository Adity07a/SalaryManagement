
import {
  Box,
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from "@mui/material";

import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import QueryStatsOutlinedIcon from "@mui/icons-material/QueryStatsOutlined";

import {
  Link as RouterLink,
  useLocation,
} from "react-router-dom";

export const DRAWER_WIDTH = 248;

const navigationItems = [
  {
    label: "Employees",
    path: "/employees",
    icon: <GroupsOutlinedIcon />,
  },
  {
    label: "Salary Insights",
    path: "/insights",
    icon: <QueryStatsOutlinedIcon />,
  },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,

        "& .MuiDrawer-paper": {
          width: DRAWER_WIDTH,
          boxSizing: "border-box",
          top: "68px",
          height: "calc(100% - 68px)",
          borderRight: 1,
          borderColor: "divider",
          p: 2,
        },
      }}
    >
      <Typography
        variant="overline"
        color="text.secondary"
        sx={{ px: 1.5, mb: 1 }}
      >
        WORKSPACE
      </Typography>

      <List disablePadding>
        {navigationItems.map((item) => {
          const selected = location.pathname.startsWith(
            item.path,
          );

          return (
            <ListItemButton
              key={item.path}
              component={RouterLink}
              to={item.path}
              selected={selected}
              sx={{
                borderRadius: 2,
                mb: 0.5,

                "&.Mui-selected": {
                  bgcolor: "primary.light",
                  color: "primary.dark",
                },

                "&.Mui-selected:hover": {
                  bgcolor: "primary.light",
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 38,
                  color: selected
                    ? "primary.dark"
                    : "text.secondary",
                }}
              >
                {item.icon}
              </ListItemIcon>

              <ListItemText
                primary={item.label}
                primaryTypographyProps={{
                  fontSize: 14,
                  fontWeight: selected ? 650 : 500,
                }}
              />
            </ListItemButton>
          );
        })}
      </List>

      <Box sx={{ flexGrow: 1 }} />

      <Divider sx={{ my: 2 }} />

      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ px: 1 }}
      >
        ACME Salary Management
      </Typography>
    </Drawer>
  );
}
