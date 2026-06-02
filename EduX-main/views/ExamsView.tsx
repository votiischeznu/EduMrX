import Text from "@/components/ui/Text";
import Title from "@/components/ui/Title";

export default function ExamsView() {
  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="">
          <Title text="Exams" />
          <Text text="Manage schedules, grading, and performance tracking across all courses." />
        </div>
      </div>
    </div>
  )
}
