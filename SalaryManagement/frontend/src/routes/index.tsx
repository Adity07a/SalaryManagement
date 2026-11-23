
import {
  createBrowserRouter,
  Navigate,
} from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";

import { EmployeesPage } from "../features/employees/pages/EmployeesPage";
import { EmployeeDetailPage } from "../features/employees/pages/EmployeeDetailPage";
import { InsightsPage } from "../features/insights/pages/InsightsPage";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,

    children: [
      {
        path: "/",
        element: <Navigate to="/employees" replace />,
      },

      {
        path: "/employees",
        element: <EmployeesPage />,
      },

      {
        path: "/employees/:employeeId",
        element: <EmployeeDetailPage />,
      },

      {
        path: "/insights",
        element: <InsightsPage />,
      },
    ],
  },
]);
