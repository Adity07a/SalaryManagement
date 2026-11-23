
import { createTheme } from "@mui/material/styles";

export const appTheme = createTheme({
  palette: {
    mode: "light",

    primary: {
      main: "#2457C5",
      dark: "#19439C",
      light: "#EAF0FF",
    },

    secondary: {
      main: "#64748B",
    },

    background: {
      default: "#F6F8FC",
      paper: "#FFFFFF",
    },

    text: {
      primary: "#182230",
      secondary: "#667085",
    },

    divider: "#E5EAF1",

    success: {
      main: "#16865B",
    },

    error: {
      main: "#D14343",
    },
  },

  typography: {
    fontFamily: [
      "Inter",
      "Roboto",
      "Arial",
      "sans-serif",
    ].join(","),

    h4: {
      fontSize: "1.75rem",
      fontWeight: 700,
      letterSpacing: "-0.5px",
    },

    h5: {
      fontSize: "1.35rem",
      fontWeight: 650,
    },

    h6: {
      fontSize: "1.05rem",
      fontWeight: 650,
    },

    button: {
      textTransform: "none",
      fontWeight: 600,
    },
  },

  shape: {
    borderRadius: 10,
  },

  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: "8px 16px",
        },
      },
    },

    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
        },
      },
    },
  },
});
