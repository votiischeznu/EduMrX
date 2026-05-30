import AttendanceOverview from "@/components/ui/DashboardChart";
import Text from "@/components/ui/Text";
import Title from "@/components/ui/Title";
import { icons } from "@/constants/icons";
import Image from "next/image";

export default function DashboardSection() {
    const status = [
        {
            id: 1,
            icon: icons.studentsIcon,
            label: "Total Students",
            degree: "1,248",
            color: "#D8E2FF"
        },
        {
            id: 2,
            icon: icons.groupsIcon,
            label: "Active Groups",
            degree: "85",
            color: "#E2DFFF"
        },
        {
            id: 3,
            icon: icons.paymentsIcon,
            label: "Monthly Income",
            degree: "$12,560",
            color: "#E1E3E4"
        },
        {
            id: 4,
            icon: icons.attendanceIcon,
            label: "Attendance Rate",
            degree: "92%",
            color: "#FFDAD6"
        },
    ]

    return (
        <div className="">
            <div className="">
                <div className="mb-[32px]">
                    <Title text="Dashboard Overview" />
                    <Text text="Welcome back, John. Here's what's happening today." />
                </div>
            </div>

            <div className="grid grid-cols-4 gap-[20px] mb-[44px]">
                {
                    status.map((item) => {
                        return (
                            <div key={item.id} className="p-6 border border-[#C7C4D8] shadow-[0_2px_4px_-2px_#1E293B] rounded-lg">
                                <div
                                    style={{ backgroundColor: item.color }} className={` w-[50px] h-[50px] rounded-lg mb-[16px] flex items-center justify-center`}>
                                    <Image
                                        src={item.icon} alt={item.label} className="w-[24px] h-[16px]" />
                                </div>
                                <div className="">
                                    <Text text={item.label} />
                                    <h2 className="text-[32px]  font-bold text-[#191C1D]">
                                        {item.degree}
                                    </h2>
                                </div>
                            </div>
                        )
                    })
                }
            </div>

            <div className="">
                <AttendanceOverview />
            </div>
        </div>
    )
}
