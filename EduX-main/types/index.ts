export interface IAPIResponse<T> {
  count: number;
  total_pages: number;
  current_page: number;
  next: string;
  previous: string;
  results: T;
}

export interface IGroupData {
  id: string;
  name: string;
  course: string;
  teacher: string;
  room: string;
  status: string;
  start_date: string;
  end_date: string;
  lesson_days: string;
  lesson_start_time: string;
  lesson_end_time: string;
  student_count: number;
  capacity: number;
  is_full: boolean;
}

// @/types/index.ts faylida
export interface IStudent {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  email: string;
  date_of_birth: string;
  address: string;
  status: "active" | "inactive" | "pending";
  notes?: string;
  latitude?: string;
  longitude?: string;
  center?: { id: string; name: string };
}

export interface ILearningCenter {
  id: string;
  name: string;
  slug: string;
  logo: string;
  phone: string;
  email: string;
  address: string;
  status: string;
  director_name: string;
  students_count: number;
  subscription_expires: string;
}

export interface IDirector {
  id: string;
  full_name: string;
  phone: string;
  email: string;
  avatar: string;
  created_at: string;
}

export interface ITeacher {
  id: string;
  full_name: string;
  avatar: string;
  phone: string;
  email: string;
  specialization: string;
  experience: number;
}
