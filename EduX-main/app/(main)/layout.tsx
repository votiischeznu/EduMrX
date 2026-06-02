"use client";

import Header from "@/components/common/Header";
import LeftComponent from "@/components/common/LeftComponent";
import ProtectedRoute from "@/components/ProtectedRoute";

export default function MailLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ProtectedRoute>
      <div className="bg-[#F8F9FAFF] min-h-screen flex flex-col">
        <aside className="bg-white  border-r border-gray-200 shadow-sm fixed left-0 top-0 h-screen w-60 z-20">
          <LeftComponent />
        </aside>

        <header className="bg-white fixed top-0 left-60 right-0 z-50 max-[1150px]:left-0">
          <Header />
        </header>

        <main className="p-[30px_30px_0_30px] ml-60 max-[1150px]:ml-0 mt-20 min-h-screen">
          {children}
        </main>
      </div>
    </ProtectedRoute>
  );
}