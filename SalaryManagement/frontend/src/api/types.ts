
export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details: unknown;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface EmployeeFields {
  full_name: string;
  email: string;
  job_title: string;
  department: string;
  country: string;
  employment_type: string;
  hire_date: string;
}

export interface SalaryRecord {
  id: number;
  employee_id: number;
  amount: string;
  currency: string;
  effective_from: string;
  amount_usd: string;
  created_at: string;
}

export interface Employee extends EmployeeFields {
  id: number;
  created_at: string;
  updated_at: string;
  current_salary: SalaryRecord | null;
}

export interface EmployeeDetail extends Employee {
  salary_history: SalaryRecord[];
}

export interface InitialSalaryPayload {
  amount: string;
  currency: string;
  effective_from: string;
}

export interface CreateEmployeePayload extends EmployeeFields {
  initial_salary: InitialSalaryPayload;
}

export type UpdateEmployeePayload = EmployeeFields;

export interface AddSalaryPayload {
  amount: string;
  currency: string;
  effective_from: string;
}

export interface EmployeeListParams {
  page: number;
  page_size: number;
  search?: string;
  country?: string;
  department?: string;
  job_title?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface MetaFilters {
  countries: string[];
  departments: string[];
  job_titles: string[];
}

export type SalaryGroupBy = "country" | "department" | "job_title";

export interface SalaryStatsGroup {
  group_value: string;
  count: number;
  min_usd: string;
  p25_usd: string;
  median_usd: string;
  p75_usd: string;
  max_usd: string;
  avg_usd: string;
}

export interface SalaryStatsResponse {
  group_by: SalaryGroupBy;
  items: SalaryStatsGroup[];
}

export interface SummaryResponse {
  headcount: number;
  total_payroll_usd: string;
  average_salary_usd: string;
  median_salary_usd: string;
}

export interface DistributionBucket {
  bucket_start_usd: string;
  bucket_end_usd: string;
  count: number;
}

export interface DistributionResponse {
  buckets: DistributionBucket[];
}

export interface SalaryOutlier {
  employee_id: number;
  full_name: string;
  job_title: string;
  department: string;
  country: string;
  salary_usd: string;
  peer_median_usd: string;
  deviation_percent: string;
  direction: "high" | "low";
}

export interface OutliersResponse {
  group_by: SalaryGroupBy;
  items: SalaryOutlier[];
}
