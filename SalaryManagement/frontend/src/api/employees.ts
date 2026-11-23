
import { apiRequest } from "./client";

import type {
    AddSalaryPayload,
    CreateEmployeePayload,
    Employee,
    EmployeeDetail,
    EmployeeListParams,
    MetaFilters,
    PaginatedResponse,
    SalaryRecord,
    UpdateEmployeePayload,
  } from "./types";
  
function buildQueryString(params: object): string {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });

  return query.toString();
}

export const employeeApi = {
  async list(
    params: EmployeeListParams,
    signal?: AbortSignal,
  ): Promise<PaginatedResponse<Employee>> {
    const query = buildQueryString(params);

    return apiRequest<PaginatedResponse<Employee>>(
      `/employees?${query}`,
      { signal },
    );
  },

  async getById(
    id: number,
    signal?: AbortSignal,
  ): Promise<EmployeeDetail> {
    return apiRequest<EmployeeDetail>(
      `/employees/${id}`,
      { signal },
    );
  },

  async create(
    payload: CreateEmployeePayload,
  ): Promise<Employee> {
    return apiRequest<Employee>("/employees", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async update(
    id: number,
    payload: UpdateEmployeePayload,
  ): Promise<Employee> {
    return apiRequest<Employee>(`/employees/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async remove(id: number): Promise<void> {
    return apiRequest<void>(`/employees/${id}`, {
      method: "DELETE",
    });
  },

  async addSalary(
    id: number,
    payload: AddSalaryPayload,
  ): Promise<SalaryRecord> {
    return apiRequest<SalaryRecord>(
      `/employees/${id}/salary`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },

  async getFilters(
    signal?: AbortSignal,
  ): Promise<MetaFilters> {
    return apiRequest<MetaFilters>(
      "/meta/filters",
      { signal },
    );
  },
};
