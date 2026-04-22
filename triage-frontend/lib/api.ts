import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

export interface AnswerPayload {
  question_id: string;
  answer_value: string;
}

export interface AssessRequest {
  zone_id: string;
  answers: AnswerPayload[];
  notes?: string;
  session_token?: string;
}

export interface AssessResult {
  session_id: string;
  triage_level: number;
  triage_label: string;
  assessment: string;
  treatment: string;
  next_steps: string[];
  red_flag: boolean;
  possible_conditions: string[];
  confidence: number;
  disclaimer: string;
}

export interface FlowOption {
  label: string;
  value: string;
  urgency: number;
  next_node: string | null;
  red_flag: boolean;
  diagnoses: string[];
  treatment: string;
}

export interface FlowNode {
  question: string;
  options: FlowOption[];
  subregion: boolean;
}

export interface FlowTree {
  [nodeId: string]: FlowNode;
}

export interface VisitSummary {
  session_id: string;
  generated_at: string;
  body_area: string;
  main_complaint: string;
  symptom_path: string[];
  red_flags_detected: string[];
  possible_conditions: string[];
  treatment_recommendation: string;
  triage_level: number;
  triage_label: string;
  timestamp: string;
  plain_text: string;
  disclaimer: string;
}

export interface Facility {
  name: string;
  address: string;
  phone?: string;
  distance_km: number;
  facility_type: string;
  lat: number;
  lng: number;
  maps_url?: string;
  open_now?: boolean;
}

export interface FacilitiesResult {
  triage_level: number;
  facility_type_label: string;
  facilities: Facility[];
  source: string;
}

export interface ProfilePayload {
  age?: number;
  biological_sex?: string;
  allergies?: string[];
  chronic_conditions?: string[];
  current_medications?: string[];
  past_surgeries?: string[];
  onboarding_complete?: boolean;
}

export const api = {
  getQuestions: async (zoneId: string): Promise<{ zone_id: string; flow: FlowTree }> => {
    const res = await client.get(`/api/questions/${zoneId}`);
    return res.data;
  },

  assess: async (payload: AssessRequest): Promise<AssessResult> => {
    const res = await client.post('/api/assess', payload);
    return res.data;
  },

  getSummary: async (sessionId: string): Promise<VisitSummary> => {
    const res = await client.get(`/api/summary/${sessionId}`);
    return res.data;
  },

  getFacilities: async (
    lat: number,
    lng: number,
    triageLevel: number,
    radiusM = 8000
  ): Promise<FacilitiesResult> => {
    const res = await client.get('/api/facilities', {
      params: { lat, lng, triage_level: triageLevel, radius_m: radiusM },
    });
    return res.data;
  },

  upsertProfile: async (payload: ProfilePayload): Promise<void> => {
    await client.put('/api/profile', payload);
  },

  getProfile: async (): Promise<ProfilePayload> => {
    const res = await client.get('/api/profile');
    return res.data;
  },
};