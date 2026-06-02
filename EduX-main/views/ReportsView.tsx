import Text from "@/components/ui/Text";
import Title from "@/components/ui/Title";

export default function ReportsView() {
  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="">
          <Title text="Reports" />
          <Text text="Analyze your institution's performance and generate detailed summaries." />
        </div>
      </div>
    </div>
  )
}
