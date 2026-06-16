import axios from "axios";
import { getToken } from "./auth";

const API_BASE = "http://localhost:8000";
const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use(async (config) => {
  const token = await getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export interface UserProfile {
  id: string; phone: string | null; nickname: string | null;
  gender: string | null; birth_year: number | null; playing_years: number | null;
  self_rated_ntrp: number | null; target_ntrp: number | null;
  handedness: string | null; injury_history: string[] | null;
}

export const login = (phone: string, password: string) =>
  api.post("/auth/login", { phone, password }).then(r => r.data);

export const register = (phone: string, password: string) =>
  api.post("/auth/register", { phone, password }).then(r => r.data);

export const getProfile = () => api.get("/users/me").then(r => r.data);

export const updateProfile = (p: Partial<UserProfile>) =>
  api.patch("/users/me", p).then(r => r.data);

export const uploadVideo = async (fileUri: string, fileName: string) => {
  const formData = new FormData();
  formData.append("file", { uri: fileUri, name: fileName, type: "video/mp4" } as any);
  return api.post("/videos/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then(r => r.data);
};

export const submitOppoWorkout = (rawData: object) =>
  api.post("/health/workouts", { raw_data: rawData }).then(r => r.data);

export const listWorkouts = () => api.get("/health/workouts").then(r => r.data);

export const startAnalysis = (videoId: string, workoutId?: string) =>
  api.post("/analysis/start", { video_id: videoId, health_workout_id: workoutId || null }).then(r => r.data);

export const listAssessments = () => api.get("/analysis/assessments").then(r => r.data);

export const getAssessment = (id: string) => api.get(`/analysis/assessments/${id}`).then(r => r.data);

export const listTrainingPlans = () => api.get("/training/plans").then(r => r.data);

export const getTrainingPlan = (id: string) => api.get(`/training/plans/${id}`).then(r => r.data);
