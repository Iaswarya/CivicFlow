/**
 * Single axios instance + typed API service layer.
 * Every backend call in the app goes through here -- no hard-coded URLs elsewhere,
 * no duplicate fetch logic in components.
 */
import axios, { AxiosError } from "axios";
import type {
  User, Product, Inspection, ProductImage, OCRResult, ExtractedField,
  ComplianceResult, AnalyticsOverview, Violation,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const apiClient = axios.create({ baseURL: BASE_URL });

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("civicflow_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let onAuthExpired: (() => void) | null = null;
export function registerAuthExpiredHandler(handler: () => void) {
  onAuthExpired = handler;
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && onAuthExpired) {
      onAuthExpired();
    }
    return Promise.reject(error);
  }
);

export function extractErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: string } | undefined)?.detail;
    if (detail) return detail;
    if (err.message === "Network Error") return "Could not reach the CivicFlow server. Is the backend running?";
    return err.message;
  }
  return "Something went wrong. Please try again.";
}

// ---------------- Auth ----------------

export const authApi = {
  register: (data: { full_name: string; email: string; password: string; role: string }) =>
    apiClient.post<{ access_token: string; user: User }>("/api/auth/register", data),
  login: (data: { email: string; password: string }) =>
    apiClient.post<{ access_token: string; user: User }>("/api/auth/login", data),
  me: () => apiClient.get<User>("/api/auth/me"),
};

// ---------------- Products ----------------

export const productsApi = {
  list: (params?: { category?: string; search?: string }) =>
    apiClient.get<Product[]>("/api/products", { params }),
  get: (id: string) => apiClient.get<Product>(`/api/products/${id}`),
  create: (data: Partial<Product>) => apiClient.post<Product>("/api/products", data),
  update: (id: string, data: Partial<Product>) => apiClient.put<Product>(`/api/products/${id}`, data),
  remove: (id: string) => apiClient.delete(`/api/products/${id}`),
};

// ---------------- Inspections ----------------

export const inspectionsApi = {
  list: (params?: Record<string, string>) => apiClient.get<Inspection[]>("/api/inspections", { params }),
  get: (id: string) => apiClient.get<Inspection>(`/api/inspections/${id}`),
  create: (data: { product_id?: string; latitude?: number; longitude?: number; location_address?: string; notes?: string }) =>
    apiClient.post<Inspection>("/api/inspections", data),
  update: (id: string, data: Partial<Inspection>) => apiClient.put<Inspection>(`/api/inspections/${id}`, data),
  remove: (id: string) => apiClient.delete(`/api/inspections/${id}`),
};

// ---------------- Images ----------------

export const imagesApi = {
  upload: (inspectionId: string, file: File, imageType: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("image_type", imageType);
    return apiClient.post<ProductImage>(`/api/inspections/${inspectionId}/images`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  list: (inspectionId: string) => apiClient.get<ProductImage[]>(`/api/inspections/${inspectionId}/images`),
};

// ---------------- OCR ----------------

export const ocrApi = {
  run: (inspectionId: string) => apiClient.post<OCRResult[]>(`/api/ocr/${inspectionId}`),
  get: (inspectionId: string) => apiClient.get<OCRResult[]>(`/api/ocr/${inspectionId}`),
};

// ---------------- Extraction ----------------

export const extractionApi = {
  run: (inspectionId: string) => apiClient.post<ExtractedField[]>(`/api/extraction/${inspectionId}`),
  get: (inspectionId: string) => apiClient.get<ExtractedField[]>(`/api/extraction/${inspectionId}`),
  correctField: (inspectionId: string, fieldId: string, value: string) =>
    apiClient.put<ExtractedField>(`/api/extraction/${inspectionId}/fields/${fieldId}`, { field_value: value }),
};

// ---------------- Compliance ----------------

export const complianceApi = {
  run: (inspectionId: string) => apiClient.post<ComplianceResult>(`/api/compliance/${inspectionId}`),
  get: (inspectionId: string) => apiClient.get<ComplianceResult>(`/api/compliance/${inspectionId}`),
  reviewViolation: (inspectionId: string, violationId: string, data: Partial<Violation>) =>
    apiClient.put<Violation>(`/api/compliance/${inspectionId}/violations/${violationId}`, data),
};

// ---------------- Reports ----------------

export const reportsApi = {
  pdfUrl: (inspectionId: string) => `${BASE_URL}/api/reports/${inspectionId}/pdf`,
  downloadPdf: (inspectionId: string) =>
    apiClient.get(`/api/reports/${inspectionId}/pdf`, { responseType: "blob" }),
};

// ---------------- Analytics ----------------

export const analyticsApi = {
  overview: () => apiClient.get<AnalyticsOverview>("/api/analytics/overview"),
  violations: () => apiClient.get("/api/analytics/violations"),
  trends: () => apiClient.get("/api/analytics/trends"),
  categories: () => apiClient.get("/api/analytics/categories"),
};
