"use client";



import { useState, useEffect, useRef } from "react";
import {
  Search,
  ChevronDown,
  SlidersHorizontal,
  Pencil,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import Title from "@/components/ui/Title";
import Text from "@/components/ui/Text";
import Image from "next/image";
import { icons } from "@/constants/icons";

type Status = "Active" | "Inactive" | "Frozen";

interface Student {
  id: string;
  studentId: string;
  name: string;
  avatar?: string;
  group: string;
  course: string;
  phone: string;
  email: string;
  balance: number;
  status: Status;
}

// ── Mock data (API_URL env set bo'lgach bu qism o'chiriladi) ───
const MOCK_STUDENTS: Student[] = [
  { id: "1", studentId: "STU-2023-001", name: "Sarah Jenkins", group: "Math 101 - A", course: "Mathematics", phone: "+1 (555) 123-4567", email: "sarah.j@example.com", balance: 0, status: "Active" },
  { id: "2", studentId: "STU-2023-042", name: "Marcus Johnson", group: "English 201 - B", course: "Literature", phone: "+1 (555) 987-6543", email: "mjohnson@example.com", balance: 150, status: "Active" },
  { id: "3", studentId: "STU-2023-018", name: "David Chen", group: "Physics 301", course: "Science", phone: "+1 (555) 456-7890", email: "d.chen@example.com", balance: 0, status: "Inactive" },
  { id: "4", studentId: "STU-2023-007", name: "Jasur Aliyev", group: "Math 101 - B", course: "Mathematics", phone: "+998901112233", email: "j.aliyev@example.com", balance: -200000, status: "Active" },
  { id: "5", studentId: "STU-2023-015", name: "Malika Karimova", group: "Math 101 - A", course: "Mathematics", phone: "+998902223344", email: "m.karimova@example.com", balance: 500000, status: "Active" },
  { id: "6", studentId: "STU-2023-023", name: "Zulfiya Rahimova", group: "English 201 - A", course: "Literature", phone: "+998906667788", email: "z.rahimova@example.com", balance: -600000, status: "Active" },
  { id: "7", studentId: "STU-2023-031", name: "Bobur Toshmatov", group: "Physics 301", course: "Science", phone: "+998907778899", email: "b.toshmatov@example.com", balance: 300000, status: "Active" },
  { id: "8", studentId: "STU-2023-039", name: "Kamola Umarova", group: "Math 101 - B", course: "Mathematics", phone: "+998908889900", email: "k.umarova@example.com", balance: 0, status: "Inactive" },
  { id: "9", studentId: "STU-2023-047", name: "Amir Saidov", group: "English 201 - B", course: "Literature", phone: "+998909990011", email: "a.saidov@example.com", balance: -350000, status: "Active" },
  { id: "10", studentId: "STU-2023-055", name: "Dildora Mirzayeva", group: "Physics 301", course: "Science", phone: "+998900001122", email: "d.mirzayeva@example.com", balance: 100000, status: "Active" },
  { id: "11", studentId: "STU-2023-062", name: "Otabek Rustamov", group: "Math 101 - A", course: "Mathematics", phone: "+998903334455", email: "o.rustamov@example.com", balance: 0, status: "Active" },
  { id: "12", studentId: "STU-2023-071", name: "Nilufar Abdullayeva", group: "English 201 - A", course: "Literature", phone: "+998904445566", email: "n.abdullayeva@example.com", balance: -400000, status: "Frozen" },
];

const ALL_GROUPS = ["All Groups", "Math 101 - A", "Math 101 - B", "English 201 - A", "English 201 - B", "Physics 301"];
const ALL_COURSES = ["All Courses", "Mathematics", "Literature", "Science"];
const ALL_STATUSES: string[] = ["Any Status", "Active", "Inactive", "Frozen"];

const PAGE_SIZE = Number(process.env.NEXT_PUBLIC_PAGE_SIZE ?? 5);

// ── Helpers ────────────────────────────────────────────────────
function getInitials(name: string) {
  return name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase();
}

const AVATAR_COLORS = [
  { bg: "#E8E4FB", text: "#5B4EBF" },
  { bg: "#D6F0FF", text: "#1A7AB5" },
  { bg: "#D6F7ED", text: "#1A7A55" },
  { bg: "#FFE8D6", text: "#B55A1A" },
  { bg: "#FFD6E8", text: "#B51A55" },
];

function avatarColor(name: string) {
  const idx = name.charCodeAt(0) % AVATAR_COLORS.length;
  return AVATAR_COLORS[idx];
}

function formatBalance(amount: number) {
  if (amount === 0) return { text: "$0.00", color: "#1a1a1a" };
  const abs = Math.abs(amount);
  const formatted =
    abs >= 1000
      ? abs.toLocaleString("en-US")
      : abs.toFixed(2);
  return {
    text: amount < 0 ? `-$${formatted}` : `$${formatted}`,
    color: amount < 0 ? "#E02424" : amount > 0 ? "#E02424" : "#1a1a1a",
  };
}

// ── Dropdown ───────────────────────────────────────────────────
function Dropdown({
  value,
  options,
  onChange,
}: {
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "10px 16px",
          border: "1.5px solid #D1D5DB",
          borderRadius: 10,
          background: "#fff",
          fontSize: 14,
          color: "#374151",
          cursor: "pointer",
          whiteSpace: "nowrap",
          fontWeight: 500,
          transition: "border-color .15s",
        }}
        onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "#9CA3AF")}
        onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "#D1D5DB")}
      >
        {value}
        <ChevronDown size={14} color="#6B7280" />
      </button>

      {open && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            minWidth: "100%",
            background: "#fff",
            border: "1.5px solid #E5E7EB",
            borderRadius: 10,
            boxShadow: "0 4px 16px rgba(0,0,0,.08)",
            zIndex: 50,
            overflow: "hidden",
          }}
        >
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => { onChange(opt); setOpen(false); }}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: "9px 16px",
                fontSize: 14,
                fontWeight: opt === value ? 600 : 400,
                color: opt === value ? "#4F46E5" : "#374151",
                background: opt === value ? "#F5F3FF" : "transparent",
                border: "none",
                cursor: "pointer",
              }}
              onMouseEnter={(e) => {
                if (opt !== value) (e.currentTarget as HTMLElement).style.background = "#F9FAFB";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.background = opt === value ? "#F5F3FF" : "transparent";
              }}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Status Badge ───────────────────────────────────────────────
function StatusBadge({ status }: { status: Status }) {
  const map: Record<Status, { bg: string; color: string }> = {
    Active: { bg: "#D1FAE5", color: "#065F46" },
    Inactive: { bg: "#FFE4E6", color: "#9F1239" },
    Frozen: { bg: "#DBEAFE", color: "#1E40AF" },
  };
  const s = map[status];
  return (
    <span
      style={{
        display: "inline-block",
        padding: "4px 14px",
        borderRadius: 999,
        background: s.bg,
        color: s.color,
        fontSize: 13,
        fontWeight: 600,
      }}
    >
      {status}
    </span>
  );
}

// ── Avatar ─────────────────────────────────────────────────────
function Avatar({ student }: { student: Student }) {
  const c = avatarColor(student.name);
  if (student.avatar) {
    return (
      <img
        src={student.avatar}
        alt={student.name}
        style={{ width: 44, height: 44, borderRadius: "50%", objectFit: "cover", flexShrink: 0 }}
      />
    );
  }
  return (
    <div
      style={{
        width: 44, height: 44, borderRadius: "50%",
        background: c.bg,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 15, fontWeight: 700, color: c.text,
        flexShrink: 0,
      }}
    >
      {getInitials(student.name)}
    </div>
  );
}

// ── Pagination ─────────────────────────────────────────────────
function Pagination({
  total,
  page,
  pageSize,
  onChange,
}: {
  total: number;
  page: number;
  pageSize: number;
  onChange: (p: number) => void;
}) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  function pages(): (number | "...")[] {
    if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
    if (page <= 4) return [1, 2, 3, "...", totalPages];
    if (page >= totalPages - 3) return [1, "...", totalPages - 2, totalPages - 1, totalPages];
    return [1, "...", page - 1, page, page + 1, "...", totalPages];
  }

  const btnBase: React.CSSProperties = {
    width: 36, height: 36, display: "flex", alignItems: "center", justifyContent: "center",
    borderRadius: 8, border: "1.5px solid #E5E7EB", fontSize: 14, fontWeight: 500,
    cursor: "pointer", background: "#fff", color: "#374151",
    transition: "all .15s",
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      <button
        style={{ ...btnBase, opacity: page === 1 ? .4 : 1 }}
        onClick={() => page > 1 && onChange(page - 1)}
        disabled={page === 1}
        aria-label="Previous"
      >
        <ChevronLeft size={16} />
      </button>

      {pages().map((p, i) =>
        p === "..." ? (
          <span key={`e${i}`} style={{ width: 36, textAlign: "center", color: "#9CA3AF", fontSize: 14 }}>...</span>
        ) : (
          <button
            key={p}
            onClick={() => onChange(p as number)}
            style={{
              ...btnBase,
              background: p === page ? "#4F46E5" : "#fff",
              color: p === page ? "#fff" : "#374151",
              border: p === page ? "1.5px solid #4F46E5" : "1.5px solid #E5E7EB",
            }}
          >
            {p}
          </button>
        )
      )}

      <button
        style={{ ...btnBase, opacity: page === totalPages ? .4 : 1 }}
        onClick={() => page < totalPages && onChange(page + 1)}
        disabled={page === totalPages}
        aria-label="Next"
      >
        <ChevronRight size={16} />
      </button>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────
export default function StudentsPage() {
  const [search, setSearch] = useState("");
  const [group, setGroup] = useState("All Groups");
  const [course, setCourse] = useState("All Courses");
  const [status, setStatus] = useState("Any Status");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  // ── When API is ready, replace this block ──────────────────
  // useEffect(() => {
  //   setLoading(true);
  //   getStudents({ search, group, course, status, page, pageSize: PAGE_SIZE })
  //     .then(res => { setStudents(res.data); setTotal(res.total); })
  //     .finally(() => setLoading(false));
  // }, [search, group, course, status, page]);
  // ──────────────────────────────────────────────────────────

  // Mock filter (client-side)
  const filtered = MOCK_STUDENTS.filter((s) => {
    const q = search.toLowerCase();
    const matchSearch =
      !q ||
      s.name.toLowerCase().includes(q) ||
      s.studentId.toLowerCase().includes(q) ||
      s.phone.includes(q);
    const matchGroup = group === "All Groups" || s.group === group;
    const matchCourse = course === "All Courses" || s.course === course;
    const matchStatus = status === "Any Status" || s.status === status;
    return matchSearch && matchGroup && matchCourse && matchStatus;
  });

  const total = filtered.length;
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const from = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const to = Math.min(page * PAGE_SIZE, total);

  function applyFilter(fn: () => void) {
    fn();
    setPage(1);
  }

  const thStyle: React.CSSProperties = {
    padding: "14px 20px",
    fontSize: 12,
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: ".06em",
    color: "#6B7280",
    background: "#F9FAFB",
    borderBottom: "1.5px solid #E5E7EB",
    whiteSpace: "nowrap",
  };

  const tdStyle: React.CSSProperties = {
    padding: "16px 20px",
    borderBottom: "1px solid #F3F4F6",
    fontSize: 14,
    verticalAlign: "middle",
  };

  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>

      <div className="mb-[32px] flex justify-between items-center">
        <div className="">
          <Title text="Students" />
          <Text text="Manage and track student enrollment, performance, and status." />
        </div>
        <div className="">
          <button className="cursor-pointer flex items-center gap-[10px] bg-[#4F46E5] p-[8px_16px] rounded-lg">
            <Image src={icons.plusIcon} alt="plus icon" />
            <span className="text-[14px] font-semibold text-[#DAD7FF]">Add student</span>
          </button>
        </div>
      </div>

      {/* ── Filter bar ── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          background: "#F9FAFB",
          border: "1.5px solid #E5E7EB",
          borderRadius: 14,
          padding: "12px 16px",
          marginBottom: 24,
          flexWrap: "wrap",
        }}
      >
        {/* Search */}
        <div style={{ position: "relative", flex: 1, minWidth: 220 }}>
          <Search
            size={16}
            color="#9CA3AF"
            style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)" }}
          />
          <input
            value={search}
            onChange={(e) => applyFilter(() => setSearch(e.target.value))}
            placeholder="Search students by name, ID or phone..."
            style={{
              width: "100%",
              paddingLeft: 40,
              paddingRight: 16,
              paddingTop: 10,
              paddingBottom: 10,
              border: "1.5px solid #D1D5DB",
              borderRadius: 10,
              fontSize: 14,
              color: "#374151",
              outline: "none",
              background: "#fff",
              boxSizing: "border-box",
              transition: "border-color .15s",
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = "#4F46E5")}
            onBlur={(e) => (e.currentTarget.style.borderColor = "#D1D5DB")}
          />
        </div>

        <Dropdown value={group} options={ALL_GROUPS} onChange={(v) => applyFilter(() => setGroup(v))} />
        <Dropdown value={course} options={ALL_COURSES} onChange={(v) => applyFilter(() => setCourse(v))} />
        <Dropdown value={status} options={ALL_STATUSES} onChange={(v) => applyFilter(() => setStatus(v))} />

        <button
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "10px 18px",
            border: "1.5px solid #D1D5DB",
            borderRadius: 10,
            background: "#fff",
            fontSize: 14,
            fontWeight: 600,
            color: "#374151",
            cursor: "pointer",
          }}
        >
          <SlidersHorizontal size={15} />
          More
        </button>
      </div>

      {/* ── Table ── */}
      <div
        style={{
          background: "#fff",
          border: "1.5px solid #E5E7EB",
          borderRadius: 14,
          overflow: "hidden",
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ ...thStyle, textAlign: "left" }}>Student Name</th>
              <th style={{ ...thStyle, textAlign: "left" }}>Group &amp; Course</th>
              <th style={{ ...thStyle, textAlign: "left" }}>Contact</th>
              <th style={{ ...thStyle, textAlign: "right" }}>Balance</th>
              <th style={{ ...thStyle, textAlign: "center" }}>Status</th>
              <th style={{ ...thStyle, textAlign: "right" }}>Actions</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} style={{ ...tdStyle, textAlign: "center", color: "#9CA3AF", padding: 48 }}>
                  Loading...
                </td>
              </tr>
            ) : paged.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ ...tdStyle, textAlign: "center", color: "#9CA3AF", padding: 48 }}>
                  No students found.
                </td>
              </tr>
            ) : (
              paged.map((student) => {
                const bal = formatBalance(student.balance);
                return (
                  <tr
                    key={student.id}
                    style={{ cursor: "pointer", transition: "background .1s" }}
                    onMouseEnter={(e) => (e.currentTarget as HTMLElement).style.background = "#F9FAFB"}
                    onMouseLeave={(e) => (e.currentTarget as HTMLElement).style.background = "transparent"}
                  >
                    {/* Student Name */}
                    <td style={tdStyle}>
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <Avatar student={student} />
                        <div>
                          <div style={{ fontWeight: 700, fontSize: 14, color: "#111827" }}>
                            {student.name}
                          </div>
                          <div style={{ fontSize: 12, color: "#9CA3AF", marginTop: 2 }}>
                            ID: {student.studentId}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Group & Course */}
                    <td style={tdStyle}>
                      <div style={{ fontWeight: 500, color: "#374151" }}>{student.group}</div>
                      <div style={{ fontSize: 13, color: "#9CA3AF", marginTop: 2 }}>{student.course}</div>
                    </td>

                    {/* Contact */}
                    <td style={tdStyle}>
                      <div style={{ color: "#374151" }}>{student.phone}</div>
                      <div style={{ fontSize: 13, color: "#9CA3AF", marginTop: 2 }}>{student.email}</div>
                    </td>

                    {/* Balance */}
                    <td style={{ ...tdStyle, textAlign: "right" }}>
                      <span style={{ fontWeight: 700, color: bal.color }}>
                        {bal.text}
                      </span>
                    </td>

                    {/* Status */}
                    <td style={{ ...tdStyle, textAlign: "center" }}>
                      <StatusBadge status={student.status} />
                    </td>

                    {/* Actions */}
                    <td style={{ ...tdStyle, textAlign: "right" }}>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 12 }}>
                        <button
                          style={{
                            background: "none",
                            border: "none",
                            color: "#4F46E5",
                            fontSize: 14,
                            fontWeight: 600,
                            cursor: "pointer",
                            padding: 0,
                          }}
                          onClick={() => {
                            // TODO: router.push(`/students/${student.id}`)
                            alert(`View: ${student.name}`);
                          }}
                        >
                          View Profile
                        </button>

                        <button
                          style={{
                            background: "none",
                            border: "none",
                            padding: 6,
                            borderRadius: 6,
                            cursor: "pointer",
                            display: "flex",
                            color: "#6B7280",
                          }}
                          onClick={() => {
                            // TODO: open edit modal
                            alert(`Edit: ${student.name}`);
                          }}
                          aria-label="Edit"
                        >
                          <Pencil size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>

        {/* ── Footer / Pagination ── */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "14px 20px",
            borderTop: "1.5px solid #F3F4F6",
            background: "#FAFAFA",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <span style={{ fontSize: 14, color: "#6B7280" }}>
            {total === 0
              ? "No results"
              : `Showing ${from} to ${to} of ${total} results`}
          </span>

          <Pagination
            total={total}
            page={page}
            pageSize={PAGE_SIZE}
            onChange={setPage}
          />
        </div>
      </div>
    </div>
  );
}