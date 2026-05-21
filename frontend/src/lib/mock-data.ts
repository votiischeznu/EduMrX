// ============================================================
// MOCK DATA — EduMrX Education Center CRM
// ============================================================

export type Role = "admin" | "teacher" | "student" | "parent";

export interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: Role;
  avatar?: string;
}

export interface Student {
  id: string;
  name: string;
  phone: string;
  email: string;
  parentName: string;
  parentPhone: string;
  groupIds: string[];
  balance: number;
  status: "active" | "inactive" | "pending";
  enrolledDate: string;
  notes: string;
}

export interface Teacher {
  id: string;
  name: string;
  phone: string;
  email: string;
  subject: string;
  groupIds: string[];
  salary: number;
  status: "active" | "inactive";
}

export interface Group {
  id: string;
  name: string;
  subject: string;
  teacherId: string;
  schedule: string;
  time: string;
  maxStudents: number;
  studentIds: string[];
  status: "active" | "inactive" | "completed";
  monthlyFee: number;
}

export interface AttendanceRecord {
  id: string;
  studentId: string;
  groupId: string;
  date: string;
  status: "present" | "absent" | "late";
}

export interface Payment {
  id: string;
  studentId: string;
  amount: number;
  date: string;
  method: "cash" | "card" | "transfer";
  status: "paid" | "pending" | "overdue";
  description: string;
  groupId: string;
}

export interface Homework {
  id: string;
  groupId: string;
  title: string;
  description: string;
  dueDate: string;
  status: "active" | "completed";
}

// ── Teachers ──────────────────────────────────────────────────
export const teachers: Teacher[] = [
  {
    id: "t1",
    name: "Aziz Yusupov",
    phone: "+998901234567",
    email: "aziz@edumrx.uz",
    subject: "Mathematics",
    groupIds: ["g1"],
    salary: 5000000,
    status: "active",
  },
  {
    id: "t2",
    name: "Diana Petrova",
    phone: "+998901234568",
    email: "diana@edumrx.uz",
    subject: "English",
    groupIds: ["g2", "g5"],
    salary: 4500000,
    status: "active",
  },
  {
    id: "t3",
    name: "Sardor Kamolov",
    phone: "+998901234569",
    email: "sardor@edumrx.uz",
    subject: "Programming",
    groupIds: ["g3", "g4"],
    salary: 6000000,
    status: "active",
  },
];

// ── Groups ────────────────────────────────────────────────────
export const groups: Group[] = [
  {
    id: "g1",
    name: "Mathematics",
    subject: "Mathematics",
    teacherId: "t1",
    schedule: "Mon, Wed, Fri",
    time: "09:00 - 10:30",
    maxStudents: 15,
    studentIds: ["s1", "s2", "s3", "s4", "s5"],
    status: "active",
    monthlyFee: 400000,
  },
  {
    id: "g2",
    name: "English",
    subject: "English",
    teacherId: "t2",
    schedule: "Tue, Thu, Sat",
    time: "10:00 - 11:30",
    maxStudents: 12,
    studentIds: ["s2", "s4", "s6", "s7", "s8"],
    status: "active",
    monthlyFee: 500000,
  },
  {
    id: "g3",
    name: "Programming",
    subject: "Programming",
    teacherId: "t3",
    schedule: "Mon, Wed, Fri",
    time: "14:00 - 16:00",
    maxStudents: 10,
    studentIds: ["s1", "s3", "s5", "s9", "s10"],
    status: "active",
    monthlyFee: 600000,
  },
  {
    id: "g4",
    name: "Science",
    subject: "Science",
    teacherId: "t3",
    schedule: "Tue, Thu",
    time: "11:00 - 12:30",
    maxStudents: 15,
    studentIds: ["s1", "s6", "s7", "s8"],
    status: "active",
    monthlyFee: 350000,
  },
  {
    id: "g5",
    name: "IELTS",
    subject: "IELTS Preparation",
    teacherId: "t2",
    schedule: "Mon, Wed, Fri",
    time: "16:00 - 18:00",
    maxStudents: 8,
    studentIds: ["s2", "s9", "s10"],
    status: "active",
    monthlyFee: 800000,
  },
];

// ── Students ──────────────────────────────────────────────────
export const students: Student[] = [
  {
    id: "s1",
    name: "Jasur Aliyev",
    phone: "+998901112233",
    email: "jasur@mail.uz",
    parentName: "Karim Aliyev",
    parentPhone: "+998901112234",
    groupIds: ["g1", "g3", "g4"],
    balance: -200000,
    status: "active",
    enrolledDate: "2025-09-01",
    notes: "Strong in math, needs help with science",
  },
  {
    id: "s2",
    name: "Malika Karimova",
    phone: "+998902223344",
    email: "malika@mail.uz",
    parentName: "Rustam Karimov",
    parentPhone: "+998902223345",
    groupIds: ["g1", "g2", "g5"],
    balance: 500000,
    status: "active",
    enrolledDate: "2025-09-01",
    notes: "Preparing for IELTS, excellent student",
  },
  {
    id: "s3",
    name: "Otabek Rustamov",
    phone: "+998903334455",
    email: "otabek@mail.uz",
    parentName: "Nargiza Rustamova",
    parentPhone: "+998903334456",
    groupIds: ["g1", "g3"],
    balance: 0,
    status: "active",
    enrolledDate: "2025-10-15",
    notes: "Interested in competitive programming",
  },
  {
    id: "s4",
    name: "Nilufar Abdullayeva",
    phone: "+998904445566",
    email: "nilufar@mail.uz",
    parentName: "Sherzod Abdullayev",
    parentPhone: "+998904445567",
    groupIds: ["g1", "g2"],
    balance: -400000,
    status: "active",
    enrolledDate: "2025-09-15",
    notes: "Regular attendance, improving in English",
  },
  {
    id: "s5",
    name: "Sardor Nazarov",
    phone: "+998905556677",
    email: "sardor.n@mail.uz",
    parentName: "Dilshod Nazarov",
    parentPhone: "+998905556678",
    groupIds: ["g1", "g3"],
    balance: 200000,
    status: "active",
    enrolledDate: "2025-10-01",
    notes: "Good progress in both Math and Programming",
  },
  {
    id: "s6",
    name: "Zulfiya Rahimova",
    phone: "+998906667788",
    email: "zulfiya@mail.uz",
    parentName: "Bahrom Rahimov",
    parentPhone: "+998906667789",
    groupIds: ["g2", "g4"],
    balance: -600000,
    status: "active",
    enrolledDate: "2025-09-01",
    notes: "Needs attention in Science, doing well in English",
  },
  {
    id: "s7",
    name: "Bobur Toshmatov",
    phone: "+998907778899",
    email: "bobur@mail.uz",
    parentName: "Anvar Toshmatov",
    parentPhone: "+998907778800",
    groupIds: ["g2", "g4"],
    balance: 300000,
    status: "active",
    enrolledDate: "2025-11-01",
    notes: "New student, adapting well",
  },
  {
    id: "s8",
    name: "Kamola Umarova",
    phone: "+998908889900",
    email: "kamola@mail.uz",
    parentName: "Jamshid Umarov",
    parentPhone: "+998908889901",
    groupIds: ["g2", "g4"],
    balance: 0,
    status: "inactive",
    enrolledDate: "2025-09-01",
    notes: "On leave until January",
  },
  {
    id: "s9",
    name: "Amir Saidov",
    phone: "+998909990011",
    email: "amir@mail.uz",
    parentName: "Nodira Saidova",
    parentPhone: "+998909990012",
    groupIds: ["g3", "g5"],
    balance: -350000,
    status: "active",
    enrolledDate: "2025-10-01",
    notes: "Talented programmer, aiming for IELTS 7.0",
  },
  {
    id: "s10",
    name: "Dildora Mirzayeva",
    phone: "+998900001122",
    email: "dildora@mail.uz",
    parentName: "Ulugbek Mirzayev",
    parentPhone: "+998900001123",
    groupIds: ["g3", "g5"],
    balance: 100000,
    status: "pending",
    enrolledDate: "2026-01-10",
    notes: "New enrollment, documents pending",
  },
];

// ── Attendance Data ────────────────────────────────────────────
function generateAttendance(): AttendanceRecord[] {
  const records: AttendanceRecord[] = [];
  const statuses: Array<"present" | "absent" | "late"> = ["present", "absent", "late"];
  let id = 1;

  // Generate 4 weeks of data
  const dates = [
    "2026-05-05", "2026-05-06", "2026-05-07", "2026-05-08", "2026-05-09",
    "2026-05-12", "2026-05-13", "2026-05-14", "2026-05-15", "2026-05-16",
    "2026-05-19", "2026-05-20", "2026-05-21",
  ];

  for (const group of groups) {
    for (const date of dates) {
      for (const studentId of group.studentIds) {
        const rand = Math.random();
        const status = rand > 0.85 ? "absent" : rand > 0.75 ? "late" : "present";
        records.push({
          id: `a${id++}`,
          studentId,
          groupId: group.id,
          date,
          status,
        });
      }
    }
  }

  return records;
}

export const attendanceRecords: AttendanceRecord[] = generateAttendance();

// ── Payments ──────────────────────────────────────────────────
export const payments: Payment[] = [
  // March payments
  { id: "p1", studentId: "s1", amount: 400000, date: "2026-03-05", method: "cash", status: "paid", description: "Mathematics - March", groupId: "g1" },
  { id: "p2", studentId: "s1", amount: 600000, date: "2026-03-05", method: "cash", status: "paid", description: "Programming - March", groupId: "g3" },
  { id: "p3", studentId: "s2", amount: 500000, date: "2026-03-03", method: "card", status: "paid", description: "English - March", groupId: "g2" },
  { id: "p4", studentId: "s2", amount: 800000, date: "2026-03-03", method: "card", status: "paid", description: "IELTS - March", groupId: "g5" },
  { id: "p5", studentId: "s3", amount: 400000, date: "2026-03-10", method: "transfer", status: "paid", description: "Mathematics - March", groupId: "g1" },
  { id: "p6", studentId: "s4", amount: 400000, date: "2026-03-15", method: "cash", status: "paid", description: "Mathematics - March", groupId: "g1" },
  { id: "p7", studentId: "s5", amount: 600000, date: "2026-03-08", method: "transfer", status: "paid", description: "Programming - March", groupId: "g3" },
  { id: "p8", studentId: "s6", amount: 500000, date: "2026-03-12", method: "cash", status: "paid", description: "English - March", groupId: "g2" },
  { id: "p9", studentId: "s7", amount: 350000, date: "2026-03-05", method: "card", status: "paid", description: "Science - March", groupId: "g4" },
  { id: "p10", studentId: "s9", amount: 600000, date: "2026-03-07", method: "transfer", status: "paid", description: "Programming - March", groupId: "g3" },

  // April payments
  { id: "p11", studentId: "s1", amount: 400000, date: "2026-04-03", method: "cash", status: "paid", description: "Mathematics - April", groupId: "g1" },
  { id: "p12", studentId: "s2", amount: 500000, date: "2026-04-02", method: "card", status: "paid", description: "English - April", groupId: "g2" },
  { id: "p13", studentId: "s2", amount: 800000, date: "2026-04-02", method: "card", status: "paid", description: "IELTS - April", groupId: "g5" },
  { id: "p14", studentId: "s3", amount: 400000, date: "2026-04-08", method: "transfer", status: "paid", description: "Mathematics - April", groupId: "g1" },
  { id: "p15", studentId: "s5", amount: 400000, date: "2026-04-05", method: "cash", status: "paid", description: "Mathematics - April", groupId: "g1" },
  { id: "p16", studentId: "s6", amount: 500000, date: "2026-04-10", method: "cash", status: "paid", description: "English - April", groupId: "g2" },
  { id: "p17", studentId: "s7", amount: 500000, date: "2026-04-04", method: "card", status: "paid", description: "English - April", groupId: "g2" },
  { id: "p18", studentId: "s10", amount: 600000, date: "2026-04-12", method: "transfer", status: "paid", description: "Programming - April", groupId: "g3" },

  // May payments
  { id: "p19", studentId: "s1", amount: 400000, date: "2026-05-02", method: "cash", status: "paid", description: "Mathematics - May", groupId: "g1" },
  { id: "p20", studentId: "s2", amount: 500000, date: "2026-05-01", method: "card", status: "paid", description: "English - May", groupId: "g2" },
  { id: "p21", studentId: "s2", amount: 800000, date: "2026-05-01", method: "card", status: "paid", description: "IELTS - May", groupId: "g5" },
  { id: "p22", studentId: "s3", amount: 600000, date: "2026-05-05", method: "transfer", status: "paid", description: "Programming - May", groupId: "g3" },
  { id: "p23", studentId: "s4", amount: 500000, date: "2026-05-15", method: "cash", status: "overdue", description: "English - May", groupId: "g2" },
  { id: "p24", studentId: "s5", amount: 600000, date: "2026-05-07", method: "transfer", status: "paid", description: "Programming - May", groupId: "g3" },
  { id: "p25", studentId: "s6", amount: 350000, date: "2026-05-18", method: "cash", status: "overdue", description: "Science - May", groupId: "g4" },
  { id: "p26", studentId: "s9", amount: 800000, date: "2026-05-20", method: "transfer", status: "pending", description: "IELTS - May", groupId: "g5" },
  { id: "p27", studentId: "s9", amount: 600000, date: "2026-05-10", method: "transfer", status: "overdue", description: "Programming - May", groupId: "g3" },
  { id: "p28", studentId: "s10", amount: 800000, date: "2026-05-12", method: "card", status: "pending", description: "IELTS - May", groupId: "g5" },
];

// ── Homework ──────────────────────────────────────────────────
export const homework: Homework[] = [
  { id: "h1", groupId: "g1", title: "Chapter 5 Exercises", description: "Complete exercises 1-20 from chapter 5", dueDate: "2026-05-23", status: "active" },
  { id: "h2", groupId: "g2", title: "Essay Writing", description: "Write a 300-word essay on climate change", dueDate: "2026-05-22", status: "active" },
  { id: "h3", groupId: "g3", title: "Build a Calculator", description: "Create a calculator app using React", dueDate: "2026-05-25", status: "active" },
  { id: "h4", groupId: "g4", title: "Lab Report", description: "Write a lab report on the photosynthesis experiment", dueDate: "2026-05-21", status: "completed" },
  { id: "h5", groupId: "g5", title: "IELTS Reading Practice", description: "Complete reading test 3 and 4 from Cambridge IELTS 17", dueDate: "2026-05-24", status: "active" },
  { id: "h6", groupId: "g1", title: "Quadratic Equations Quiz", description: "Prepare for in-class quiz on quadratic equations", dueDate: "2026-05-26", status: "active" },
  { id: "h7", groupId: "g3", title: "API Integration", description: "Build a weather app using a public API", dueDate: "2026-05-28", status: "active" },
];

// ── Chart Data ────────────────────────────────────────────────
export const monthlyIncomeData = [
  { month: "Dec", income: 8200000 },
  { month: "Jan", income: 9500000 },
  { month: "Feb", income: 8800000 },
  { month: "Mar", income: 11200000 },
  { month: "Apr", income: 10500000 },
  { month: "May", income: 12800000 },
];

export const weeklyAttendanceData = [
  { day: "Mon", present: 38, absent: 4, late: 3 },
  { day: "Tue", present: 25, absent: 3, late: 2 },
  { day: "Wed", present: 37, absent: 5, late: 3 },
  { day: "Thu", present: 24, absent: 2, late: 4 },
  { day: "Fri", present: 36, absent: 6, late: 3 },
  { day: "Sat", present: 23, absent: 3, late: 1 },
];

// ── Current user (for demo) ──────────────────────────────────
export const currentUser: User = {
  id: "u1",
  name: "Admin User",
  email: "admin@edumrx.uz",
  phone: "+998901000000",
  role: "admin",
};

// ── Helper functions ──────────────────────────────────────────
export function getTeacherById(id: string): Teacher | undefined {
  return teachers.find((t) => t.id === id);
}

export function getStudentById(id: string): Student | undefined {
  return students.find((s) => s.id === id);
}

export function getGroupById(id: string): Group | undefined {
  return groups.find((g) => g.id === id);
}

export function getGroupsByTeacher(teacherId: string): Group[] {
  return groups.filter((g) => g.teacherId === teacherId);
}

export function getStudentsByGroup(groupId: string): Student[] {
  const group = getGroupById(groupId);
  if (!group) return [];
  return students.filter((s) => group.studentIds.includes(s.id));
}

export function getPaymentsByStudent(studentId: string): Payment[] {
  return payments.filter((p) => p.studentId === studentId);
}

export function getAttendanceByStudent(studentId: string): AttendanceRecord[] {
  return attendanceRecords.filter((a) => a.studentId === studentId);
}

export function getAttendanceByGroupAndDate(groupId: string, date: string): AttendanceRecord[] {
  return attendanceRecords.filter((a) => a.groupId === groupId && a.date === date);
}

export function getDebtStudents(): Student[] {
  return students.filter((s) => s.balance < 0);
}
