import Text from '@/components/ui/Text'
import Title from '@/components/ui/Title'

export default function AttendanceView() {
  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="">
          <Title text="Attendance" />
          <Text text="Manage and review daily attendance across all groups." />
        </div>
      </div>
    </div>
  )
}
