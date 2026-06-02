import Text from "@/components/ui/Text";
import Title from "@/components/ui/Title";
import { icons } from "@/constants/icons";
import Image from "next/image";

export default function CoursesView() {
  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="">
          <Title text="Courses" />
          <Text text="Manage educator profiles, department assignments, and contact details." />
        </div>

        <div className="">
          <button className="bg-[#4F46E5] cursor-pointer p-[8px_16px] flex items-center gap-[8px] rounded-lg text-white">
            <Image className="" src={icons.plusIcon} alt="plus-icon" />
            <span>Add Courses</span>
          </button>
        </div>
      </div>
    </div>
  )
}
