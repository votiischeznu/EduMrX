import { icons } from "@/constants/icons";
import { useAuthStore } from "@/store/authStore";
import Image from "next/image";

export default function Header() {
    const { user } = useAuthStore()


    return (
        <header>
            <div className="border-b border-gray-200 shadow-sm p-[24px_12px] flex justify-between items-center">
                <div className="border border-[#C7C4D8] rounded-lg max-w-[380px] gap-[10px] p-[0_0_0_12px] w-full flex items-center h-[40px]">
                    <Image src={icons.searchIcon} alt="search-icon" />
                    <input type="text" placeholder="Search students, courses..." className="outline-none text-[#6B7280]" />
                </div>

                <div className="flex items-center gap-[15px]">
                    <div className="flex items-center">
                        <span className="text-[14px] text-[#464555] border-r-[1.5px] pr-[15px] border-[#464555]">{user?.role?.toUpperCase()}</span>
                        <span className="text-[14px] text-[#464555] pl-[15px]">{user?.full_name}</span>
                    </div>
                    {
                        user?.avatar ? <Image src={user?.avatar} alt="user-avatar" className="w-[32px] h-[32px] rounded-full" /> :
                            <i className="bi bi-person-circle text-[#464555] text-[25px]"></i>
                    }
                </div>
            </div>
        </header>
    )
}
