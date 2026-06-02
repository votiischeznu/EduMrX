import Text from "@/components/ui/Text";
import Title from "@/components/ui/Title";

export default function SettingsView() {
  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="">
          <Title text="Settings" />
          <Text text="Manage your institute preferences and administrative configurations." />
        </div>
      </div>
    </div>
  )
}
