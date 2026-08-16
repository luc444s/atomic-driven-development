// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "@systutor/shell/api/client";

export type LogisticsAgendaTaskType = {
  code: string;
  description: string;
};

export type LogisticsAgendaTask = {
  id: string;
  tenant_id: string;
  route_id: string | null;
  driver_id: string;
  customer_id: string;
  customer_name: string | null;
  delivery_point_id: string | null;
  task_type: string;
  description: string | null;
  scheduled_date: string;
  scheduled_time: string | null;
  status: string;
  priority: number;
  order_id: string | null;
  quantity_requested: number | null;
  quantity_served: number | null;
  cylinder_serial: string | null;
  customer_confirmed: boolean;
  requires_signature: boolean;
  evidence_url: string | null;
  delivery_location: string | null;
  gps_coordinates: Record<string, unknown>;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export function listTaskTypes() {
  return apiRequest<LogisticsAgendaTaskType[]>(`${API_PREFIX}/catalog/task-types`);
}

export function listAgendaTasks(filters: {
  driver?: string;
  task_type?: string;
  status?: string;
  date?: string;
}) {
  return apiRequest<LogisticsAgendaTask[]>(
    withQuery(`${API_PREFIX}/agenda/tasks`, {
      driver: filters.driver,
      task_type: filters.task_type,
      status: filters.status,
      date: filters.date,
    })
  );
}

export function getAgendaTask(taskId: string) {
  return apiRequest<LogisticsAgendaTask>(`${API_PREFIX}/agenda/tasks/${taskId}`);
}

export function listAgendaTasksByDriver(driverId: string) {
  return apiRequest<LogisticsAgendaTask[]>(`${API_PREFIX}/agenda/tasks/by-driver/${driverId}`);
}

export function createAgendaTask(payload: Record<string, unknown>) {
  return apiRequest<LogisticsAgendaTask>(`${API_PREFIX}/agenda/tasks`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAgendaTask(taskId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsAgendaTask>(`${API_PREFIX}/agenda/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function completeAgendaTask(taskId: string) {
  return apiRequest<LogisticsAgendaTask>(`${API_PREFIX}/agenda/tasks/${taskId}/complete`, {
    method: "POST",
  });
}

export function cancelAgendaTask(taskId: string) {
  return apiRequest<LogisticsAgendaTask>(`${API_PREFIX}/agenda/tasks/${taskId}/cancel`, {
    method: "POST",
  });
}

export type AgendaDailySummaryBucket = {
  driver_id: string;
  status: string;
  total: number;
};

export function getAgendaDailySummary(date?: string) {
  return apiRequest<AgendaDailySummaryBucket[]>(
    withQuery(`${API_PREFIX}/agenda/daily-summary`, { date })
  );
}

export function updateAgendaTaskGps(taskId: string, payload: { gps_coordinates: Record<string, unknown> }) {
  return apiRequest<void>(`${API_PREFIX}/agenda/tasks/${taskId}/gps`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

